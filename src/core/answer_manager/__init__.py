"""Manage answer generation using retrieved documents and cached results.

This module coordinates document retrieval, prompt construction, language-model
inference, answer caching, and dataset-based answer generation.
"""

from typing import Literal, TypeAlias, cast
from pydantic import ValidationError
from src.core.utils import Logger
from src.core.entities import Document, QuestionAnswer, Question
from src.core.validation_models import (
    MinimalSearchResults,
    StudentSearchResults,
    MinimalAnswer,
    StudentSearchResultsAndAnswer,
    MinimalSource,
    UnansweredQuestion,
)
from src.core.config_manager import ConfigManager, config_manager
from src.server.errors import CustomDatabaseError
from src.core.utils import get_validation_error_message


PROMPT: str = """
    You are a helpful enterprise assistant.
    Answer the user's question using only the context provided below.
    Do not assume or extrapolate.
    If the answer is not present in the context,
    state "I cannot answer this based on the provided information."
    Context:
    {RETRIEVED_DOCUMENTS}
    Question:
    {USER_QUESTION}
    Instructions:
    Think step-by-step before answering.
    Cite the specific source document name or ID for each key claim.
"""


class AnswerError(Exception):
    """Raised when answer generation or answer processing fails."""


_PreindexingStrategy: TypeAlias = Literal["lexical", "hybrid", "none"]

MAX_TOKENS = 200


class AnswerManager:
    """Coordinate answer generation, retrieval, and answer caching.

    The manager validates the configured indexing strategy, retrieves
    relevant documents, generates answers through a language model, and
    stores generated answers for subsequent requests.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize the answer manager.

        Args:
            config_manager: Configuration manager providing the indexing
                strategy and other application settings.
        """
        self.__config_manager: ConfigManager = config_manager
        self.__text_generation_pipeline: object | None = None

    def answer(
        self,
        question: str,
        top_k: int,
        is_hybrid: bool,
        max_tokens: int
    ) -> str:
        """Generate an answer for a question or return its cached answer.

        The cached answer is reused when its retrieval parameters match
        the requested parameters. Otherwise, the question is retrieved
        again and a new answer is generated.

        Args:
            question: User question to answer.
            top_k: Maximum number of documents requested during retrieval.
            is_hybrid: Whether hybrid retrieval should be used.

        Returns:
            The generated or cached answer.

        Raises:
            AnswerError: If the indexing strategy is incompatible or
                a database operation fails.
        """
        try:
            self.__check_preindexing_strategy(is_hybrid)
            generated_answer: str
            from src.server.repositories import (
                question_repository,
                transaction_atomic,
            )

            # check if the question is already retrieved
            with transaction_atomic():
                cache_question_answer: QuestionAnswer | None = (
                    question_repository.get_question_answer(question)
                )
                if (
                    cache_question_answer is None
                    or self.__is_cache_question_answer_changed(
                        cache_question_answer,
                        top_k,
                        is_hybrid,
                        max_tokens=max_tokens
                    )
                ):
                    generated_answer = self.__answer_query_and_store_in_cache(
                        question=question,
                        is_hybrid=is_hybrid,
                        top_k=top_k,
                        max_tokens=max_tokens
                    )
                else:
                    Logger.info(
                        "The question answer is found in cache", "ANSWER"
                    )
                    generated_answer = cache_question_answer.answer
        except CustomDatabaseError as error:
            raise AnswerError(str(error)) from error
        return generated_answer

    def answer_dataset(
        self,
        student_search_results_path: str,
        max_tokens: int
    ) -> StudentSearchResultsAndAnswer:
        """Generate answers for questions contained in search results.

        Loads and validates a student's search results, verifies that
        retrieved sources correspond to the cached documents, and generates
        answers for questions that do not already have cached answers.

        Args:
            student_search_results_path: Path to the JSON file containing
                the student's search results.

        Returns:
            Search results enriched with generated or cached answers.

        Raises:
            AnswerError: If indexing is unavailable, validation fails,
                or a database operation fails.
        """
        if self.__config_manager.config.indexing_strategy == "none":
            raise AnswerError(
                "Cannot perform the search because"
                + " no indexing strategy is configured."
            )
        student_search_results: StudentSearchResults = (
            self.__load_student_search_results(student_search_results_path)
        )
        from src.server.repositories import (
            question_repository,
            transaction_atomic,
        )

        questions_answers_to_create: list[QuestionAnswer] = list()
        generated_answer: str
        prompt: str
        minimal_answers: list[MinimalAnswer] = list()
        try:
            with transaction_atomic():
                for (
                    minimal_search_results
                ) in student_search_results.search_results:
                    retrieved_sources: list[MinimalSource] = (
                        minimal_search_results.retrieved_sources
                    )
                    question: str = minimal_search_results.question
                    cache_question: Question | None = question_repository.get(
                        question
                    )
                    documents: list[Document] = self.__validate_question(
                        cache_question=cache_question,
                        top_k=student_search_results.k,
                        minimal_search_results=minimal_search_results,
                    )
                    cache_question_answer: QuestionAnswer | None = (
                        question_repository.get_question_answer(question)
                    )
                    if cache_question_answer is None:
                        documents_str: str = "\n".join(
                            [document.content for document in documents]
                        )
                        prompt = self.__build_prompt(question, documents_str)
                        generated_answer = self.__generate_answer(
                            prompt,
                            max_tokens=max_tokens
                        )
                        question_answer: QuestionAnswer = QuestionAnswer(
                            question=cast(Question, cache_question),
                            answer=generated_answer,
                            max_tokens=max_tokens
                        )
                        questions_answers_to_create.append(question_answer)
                        minimal_answers.append(
                            MinimalAnswer(
                                answer=generated_answer,
                                question=question,
                                question_id=minimal_search_results.question_id,
                                retrieved_sources=retrieved_sources,
                            )
                        )
                    else:
                        retrieved_sources = (
                            minimal_search_results.retrieved_sources
                        )
                        minimal_answers.append(
                            MinimalAnswer(
                                answer=cache_question_answer.answer,
                                question=question,
                                question_id=minimal_search_results.question_id,
                                retrieved_sources=retrieved_sources,
                            )
                        )
                question_repository.create_many_questions_answers(
                    questions_answers_to_create
                )
        except CustomDatabaseError as error:
            raise AnswerError(str(error)) from error

        student_search_results_and_answers: StudentSearchResultsAndAnswer = (
            StudentSearchResultsAndAnswer(
                search_results=minimal_answers, k=student_search_results.k
            )
        )
        return student_search_results_and_answers

    def __check_preindexing_strategy(self, is_hybrid: bool) -> None:
        """Validate that the configured indexing strategy supports retrieval.

        Args:
            is_hybrid: Indicates whether hybrid retrieval is requested.

        Raises:
            AnswerError: If indexing is disabled or hybrid retrieval is
                requested with lexical-only indexing.
        """
        preindexing_strategy: _PreindexingStrategy = (
            self.__config_manager.config.indexing_strategy
        )
        match preindexing_strategy:
            case "none":
                raise AnswerError(
                    "Cannot perform the search because"
                    + " no indexing strategy is found."
                )
            case "lexical" if is_hybrid:
                raise AnswerError(
                    "Hybrid search requires a semantic "
                    + "indexing strategy, but the current "
                    + "configuration uses lexical indexing."
                    + " Configure a compatible indexing "
                    + "strategy to enable hybrid search."
                )
            case _:
                ...

    def __validate_question(
        self,
        *,
        cache_question: Question | None,
        top_k: int,
        minimal_search_results: MinimalSearchResults,
    ) -> list[Document]:
        """Validate cached question data against retrieved search results.

        Checks that the question exists, its retrieval limit matches,
        and its cached documents correspond to the retrieved sources.

        Args:
            cache_question: Cached question entity, if available.
            top_k: Requested number of retrieved documents.
            minimal_search_results: Search results containing the
                question metadata and retrieved source information.

        Returns:
            The cached documents associated with the question.

        Raises:
            AnswerError: If the question is missing or its cached retrieval
                metadata or sources do not match the supplied results.
        """
        question = (
            cache_question.question
            if cache_question is not None
            else "Unknown question"
        )

        if cache_question is None:
            raise AnswerError(
                f"Question validation failed for '{question}': "
                + "the cached question was not found."
            )
        if cache_question.top_k != top_k:
            raise AnswerError(
                f"Question validation failed for '{question}': "
                + "top_k mismatch a "
                + f"(cached={cache_question.top_k}, requested={top_k})."
            )

        from src.server.repositories import question_repository

        question_documents: list[Document] = (
            question_repository.get_question_documents(cache_question.question)
        )
        retrieved_sources = minimal_search_results.retrieved_sources
        if len(question_documents) != len(retrieved_sources):
            raise AnswerError(
                "Question validation failed for '{question}': "
                + "document count mismatch "
                + f"(cached={len(question_documents)}, "
                + f"retrieved={len(retrieved_sources)})."
            )
        for index, minimal_source in enumerate(retrieved_sources):
            if not self.__contain(minimal_source, question_documents):
                raise AnswerError(
                    f"Question validation failed for '{question}': "
                    + f"retrieved source at index {index} "
                    + "does not match any cached question document."
                )
        return question_documents

    def __contain(
        self, minimal_source: MinimalSource, cache_documents: list[Document]
    ) -> bool:
        """Check whether a retrieved source exists among cached documents.

        A source matches a document when their character boundaries and
        associated file paths are identical.

        Args:
            minimal_source: Retrieved source metadata to verify.
            cache_documents: Cached documents to compare against.

        Returns:
            True if a matching document exists, otherwise False.
        """
        for document in cache_documents:
            if (
                document.start_index == minimal_source.first_character_index
                and document.end_index == minimal_source.last_character_index
                and document.file.path == minimal_source.file_path
            ):
                return True
        return False

    def __answer_query_and_store_in_cache(
        self,
        *,
        question: str,
        is_hybrid: bool,
        top_k: int,
        max_tokens: int
    ) -> str:
        """Retrieve documents, generate an answer, and cache the result.

        Args:
            question: Question to retrieve and answer.
            is_hybrid: Whether hybrid retrieval should be used.
            top_k: Maximum number of documents to retrieve.

        Returns:
            The generated answer.

        Raises:
            AnswerError: If a database operation fails.
        """
        try:
            from src.core.search_engine import search_engine, SearchType
            from src.server.repositories import question_repository

            generated_answer: str
            search_type: SearchType = (
                SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
            )
            Logger.warn(
                "The question is not found in the cache."
                + " Running the retrieval",
                "ANSWER",
            )
            unanswered_question: UnansweredQuestion = UnansweredQuestion(
                question=question
            )
            minimal_search_results: MinimalSearchResults = search_engine(
                unanswered_question=unanswered_question,
                top_k=top_k,
                search_type=search_type,
            )
            documents: list[Document] = (
                question_repository.get_question_documents(question)
            )
            documents_str = "\n".join(
                [document.content for document in documents]
            )
            Logger.info("the question is retrieved_successfully", "ANSWER")
            prompt: str = self.__build_prompt(question, documents_str)
            generated_answer = self.__generate_answer(prompt, max_tokens)
            _question: Question = Question(
                id=minimal_search_results.question_id,
                question=question,
                top_k=top_k,
                search_type=search_type.name,
            )
            question_answer: QuestionAnswer = QuestionAnswer(
                question=_question,
                answer=generated_answer,
                max_tokens=max_tokens
            )
            question_repository.create_question_answer(question_answer)
            return generated_answer
        except CustomDatabaseError as error:
            raise AnswerError(str(error)) from error

    def __load_student_search_results(
        self, student_search_results_path: str
    ) -> StudentSearchResults:
        """Load and validate student search results from a JSON file.

        Args:
            student_search_results_path: Path to the search results file.

        Returns:
            Validated student search results.

        Raises:
            AnswerError: If the JSON content does not match the expected
                validation model.
        """
        student_search_results: StudentSearchResults
        with open(student_search_results_path, "r") as file:
            content: str = file.read()
            try:
                student_search_results = (
                    StudentSearchResults.model_validate_json(content)
                )
            except ValidationError as error:
                raise AnswerError(
                    get_validation_error_message(error, "")
                ) from error
        return student_search_results

    def __build_prompt(self, question: str, retrieved_documents: str) -> str:
        """Build the language-model prompt using a question
            and retrieved context.

        Args:
            question: User question to include in the prompt.
            retrieved_documents: Text content of the retrieved documents.

        Returns:
            A formatted prompt containing the question and context.
        """
        return PROMPT.replace(
            "{RETRIEVED_DOCUMENTS}", retrieved_documents
        ).replace("{USER_QUESTION}", question)

    @property
    def __get_text_generation_pipeline(self) -> object:
        """Return the lazily initialized text-generation pipeline.

        Initializes the Qwen3 model pipeline on first access and reuses
        the same instance for subsequent generations.

        Returns:
            The configured text-generation pipeline.
        """
        if self.__text_generation_pipeline is None:
            from transformers import pipeline
            from accelerate import Accelerator

            self.__text_generation_pipeline = pipeline(
                "text-generation",
                model="Qwen/Qwen3-0.6B",
                device=Accelerator().device,
            )
        return self.__text_generation_pipeline

    def __is_cache_question_answer_changed(
        self,
        cache_question_answer: QuestionAnswer,
        top_k: int,
        is_hybrid: bool,
        max_tokens: int
    ) -> bool:
        """Determine whether cached answer retrieval parameters are outdated.

        Compares the cached retrieval limit and search strategy against
        the parameters requested by the current operation.

        Args:
            cache_question_answer: Cached question-answer entity.
            top_k: Requested retrieval limit.
            is_hybrid: Whether hybrid retrieval is requested.

        Returns:
            True if the cached retrieval parameters differ from the
            requested parameters, otherwise False.
        """
        searching_strategy: Literal["HYBRID", "LEXICAL"] = (
            "HYBRID" if is_hybrid else "LEXICAL"
        )
        if (
            cache_question_answer.question.top_k != top_k
            or searching_strategy != cache_question_answer.question.search_type
            or cache_question_answer.max_tokens != max_tokens
        ):
            return True
        return False

    def __generate_answer(self, prompt: str, max_tokens: int) -> str:
        """Generate an answer using the configured language model.

        Args:
            prompt: Complete prompt containing the question and retrieved
                document context.

        Returns:
            Generated text with the original prompt removed.
        """
        from transformers import TextGenerationPipeline

        text_generation_pipeline: TextGenerationPipeline = cast(
            TextGenerationPipeline, self.__get_text_generation_pipeline
        )
        return text_generation_pipeline(prompt, max_new_tokens=max_tokens)[0][
            "generated_text"
        ][len(prompt):]


answer_manager: AnswerManager = AnswerManager(config_manager=config_manager)

__all__ = [
    "answer_manager",
    "AnswerManager"
]
