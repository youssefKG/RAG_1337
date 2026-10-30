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
    UnansweredQuestion
)
from src.core.config_manager import ConfigManager, config_manager

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

class QuestionNotRetrievedYetError(Exception):
    pass

class AnswerError(Exception):
    ...

_PreindexingStrategy: TypeAlias =  Literal["lexical", "hybrid", "none"]

MAX_TOKENS = 200

class AnswerManager:
    def __init__(
        self,
        config_manager: ConfigManager
    ) -> None:
        self.__config_manager: ConfigManager = config_manager
        self.__text_generation_pipeline: object | None = None

    def answer(self, question: str, top_k: int, is_hybrid: bool) -> str:
        # check if theres is somme preindexing strategy and the predindexing
        # is hybrid if the answer should be generated based on
        # sematic search and lexical search
        self.__check_preindexing_strategy(is_hybrid)
        generated_answer: str
        from src.server.repositories import question_repository
        # check if the question is already retrieved
        cache_question_answer: QuestionAnswer | None = question_repository.get_question_answer(question)
        if (
            cache_question_answer is None
            or self.__is_cache_question_answer_changed(
                cache_question_answer,
                top_k,
                is_hybrid
            )
        ):
            generated_answer = self.__answer_query_and_store_in_cache(
                question=question,
                is_hybrid=is_hybrid,
                top_k=top_k, 
                _text_generation_pipeline=self.__get_text_generation_pipeline
            )
        else:
            Logger.info("The question answer is found in cache", "ANSWER")
            generated_answer = cache_question_answer.answer
        return generated_answer

    def answer_dataset(
        self,
        student_search_results_path: str,
    ) -> StudentSearchResultsAndAnswer:
        if self.__config_manager.config.indexing_strategy == "none":
            raise AnswerError(
                "Cannot perform the search because n eo indexing strategy is configured. "
                + "Configure an indexing strategy or enable pre-indexing before searching."
            )
        student_search_results: StudentSearchResults = \
                self.__load_student_search_results(student_search_results_path)
        from src.server.repositories import question_repository
        questions_answers_to_create: list[QuestionAnswer] = list()
        generated_answer: str
        prompt: str
        minimal_answers: list[MinimalAnswer] = list()
        for minimal_search_results in student_search_results.search_results:
            question: str = minimal_search_results.question
            cache_question: Question | None = question_repository.get(question)
            documents: list[Document] = self.__validate_question(
                cache_question=cache_question,
                top_k=student_search_results.k,
                minimal_search_results=minimal_search_results
            )
            cache_question_answer: QuestionAnswer | None = \
                question_repository.get_question_answer(question)
            if cache_question_answer is None:
                documents_str: str = "\n".join([document.content for document in documents])
                prompt = self.__build_prompt(question, documents_str)
                generated_answer = self.__generate_answer(prompt)
                question_answer: QuestionAnswer = QuestionAnswer(
                    question=cast(Question, cache_question),
                    answer=generated_answer
                )
                questions_answers_to_create.append(question_answer)
                minimal_answers.append(
                    MinimalAnswer(
                        answer=generated_answer,
                        question=question,
                        question_id=minimal_search_results.question_id,
                        retrieved_sources=minimal_search_results.retrieved_sources
                    )
                )
            else:
                minimal_answers.append(
                    MinimalAnswer(
                        answer=cache_question_answer.answer,
                        question=question,
                        question_id=minimal_search_results.question_id,
                        retrieved_sources=minimal_search_results.retrieved_sources
                    )
                )
        question_repository.create_many_questions_answers(questions_answers_to_create)
        student_search_results_and_answers: StudentSearchResultsAndAnswer = \
            StudentSearchResultsAndAnswer(
                search_results=minimal_answers,
                k=student_search_results.k
            )
        return student_search_results_and_answers


    def __check_preindexing_strategy(self, is_hybrid: bool) -> None:
        preindexing_strategy: _PreindexingStrategy = self.__config_manager.config.indexing_strategy
        match preindexing_strategy:
            case "none":
                raise AnswerError(
                    "Cannot perform the search because n eo indexing strategy is configured. "
                    + "Configure an indexing strategy or enable pre-indexing before searching."
                )
            case "lexical" if is_hybrid:
                raise AnswerError(
                    "Hybrid search requires a semantic indexing strategy, but the current "
                    + "configuration uses lexical indexing. Configure a compatible indexing "
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
        question = (cache_question.question if cache_question is not None else "Unknown question")

        if cache_question is None:
            raise AnswerError(
                f"Question validation failed for '{question}': "
                + "the cached question was not found."
            )
        if cache_question.top_k != top_k:
            raise AnswerError(
                f"Question validation failed for '{question}': "
                + f"top_k mismatch (cached={cache_question.top_k}, requested={top_k})."
            )

        from src.server.repositories import question_repository
        question_documents: list[Document] = (
            question_repository.get_question_documents(cache_question.question)
        )
        retrieved_sources = minimal_search_results.retrieved_sources
        if len(question_documents) != len(retrieved_sources):
            raise AnswerError(
                f"Question validation failed for '{question}': "
                + f"document count mismatch "
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
        self,
        minimal_source: MinimalSource,
        cache_documents: list[Document]
    ) -> bool:
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
        _text_generation_pipeline: object
    ) -> str:
        from src.core.search_engine import search_engine, SearchType
        from src.server.repositories import question_repository
        generated_answer: str
        search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        Logger.warn("The question is not found in the cache. Running the retrieval", "ANSWER")
        unanswered_question: UnansweredQuestion = UnansweredQuestion(question=question)
        minimal_search_results: MinimalSearchResults = search_engine(
            unanswered_question=unanswered_question,
            top_k=top_k,
            search_type=search_type
       )
        documents: list[Document] = question_repository.get_question_documents(question)
        documents_str = "\n".join([document.content for document in documents])
        Logger.info("the question is retrieved_successfully", "ANSWER")
        prompt: str = self.__build_prompt(question, documents_str)
        generated_answer = self.__generate_answer(prompt)
        _question: Question = Question(
            id=minimal_search_results.question_id,
            question=question,
            top_k=top_k,
            search_type=search_type.name
        )
        question_answer: QuestionAnswer = QuestionAnswer(
            question=_question,
            answer=generated_answer
        )
        question_repository.create_question_answer(question_answer)
        return generated_answer

    def __load_student_search_results(
        self,
        student_search_results_path: str
    ) -> StudentSearchResults:
        student_search_results: StudentSearchResults
        with open(student_search_results_path, "r") as file:
            content: str = file.read()
            try:
                student_search_results = StudentSearchResults.model_validate_json(content)
            except ValidationError as error:
                raise AnswerError(error.errors()[0]["msg"])
        return student_search_results

    def __build_prompt(self, question: str, retrieved_documents: str) -> str:
        return (
            PROMPT
            .replace("{RETRIEVED_DOCUMENTS}", retrieved_documents)
            .replace("{USER_QUESTION}", question)
        )

    @property
    def __get_text_generation_pipeline(self) -> object:
        if self.__text_generation_pipeline is None:
            from transformers import pipeline
            from accelerate import Accelerator
            self.__text_generation_pipeline = pipeline(
                "text-generation",
                model="Qwen/Qwen3-0.6B",
                device=Accelerator().device
            )
        return self.__text_generation_pipeline

    def __is_cache_question_answer_changed(
        self,
        cache_question_answer: QuestionAnswer,
        top_k: int,
        is_hybrid: bool
    ) -> bool:
        searching_strategy: Literal["HYBRID", "LEXICAL"] = "HYBRID" if is_hybrid else "LEXICAL"
        if (
            cache_question_answer.question.top_k != top_k or
            searching_strategy != cache_question_answer.question.search_type
        ):
            return True
        return False

    def __generate_answer(self, prompt: str) -> str:
        from transformers import TextGenerationPipeline
        text_generation_pipeline: TextGenerationPipeline = cast(
            TextGenerationPipeline,
            self.__get_text_generation_pipeline
        )
        return text_generation_pipeline(prompt, max_new_tokens=MAX_TOKENS)[0]["generated_text"][len(prompt):]

answer_manager: AnswerManager = AnswerManager(
    config_manager=config_manager
)

__all__ = [
    "answer_manager",
    "AnswerManager"
]
