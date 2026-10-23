from typing import Literal
from transformers import pipeline, TextGenerationPipeline
from accelerate import Accelerator

from src.core.utils import Logger
from src.core.search_engine import SearchEngine, SearchType
from src.server.repositories import QuestionRepositoryInterface, question_repository
from src.core.entities import Document, QuestionAnswer, Question
from src.core.validation_models import UnansweredQuestion
from src.core.config_manager import ConfigManager
from src.core.search_engine import search_engine
from src.core.config_manager import config_manager

PROMPT: str = """
    You are a helpful enterprise assistant. Answer the user's question using only the context provided below. Do not assume or extrapolate. If the answer is not present in the context, state "I cannot answer this based on the provided information."
    Context:
    {RETRIEVED_DOCUMENTS}
    Question:
    {USER_QUESTION}
    Instructions:
    Think step-by-step before answering. Cite the specific source document name or ID for each key claim.
"""

class QuestionNotRetrievedYetError(Exception):
    pass


class AnswerError(Exception):
    ...

class AnswerManager:
    def __init__(
        self,
        search_engine: SearchEngine,
        question_repository: QuestionRepositoryInterface,
        config_manager: ConfigManager
    ) -> None:
        self.__search_engine: SearchEngine = search_engine
        self.__question_repository: QuestionRepositoryInterface = question_repository
        self.__config_manager: ConfigManager = config_manager

    def answer(self, question: UnansweredQuestion, top_k: int, is_hybrid: bool) -> str:
        preindexing_strategy: Literal["lexical", "hybrid", "none"] = self.__config_manager.config.indexing_strategy
        generated_answer: str
        search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        _question: Question = Question(
            id=question.question_id,
            question=question.question,
            search_type=search_type.name,
            top_k=top_k
        )
        match preindexing_strategy:
            case "none":
                raise AnswerError(
                    "Cannot perform the search because no indexing strategy is configured. "
                    + "Configure an indexing strategy or enable pre-indexing before searching."
                )
            case "lexical" if is_hybrid:
                raise AnswerError(
                    "Hybrid search requires a semantic indexing strategy, but the current "
                    + "configuration uses lexical indexing. Configure a compatible indexing "
                    + "strategy to enable hybrid search."
                )     
            case _:
                cache_question_answer: QuestionAnswer | None = self.__question_repository.get_question_answer(question.question)
                if cache_question_answer is None:
                    Logger.warn("The question is not found in the cache. Running the retrieval", "ANSWER")
                    _ = self.__search_engine(
                        question=question,
                        top_k=top_k,
                        search_type=search_type
                   )
                    documents: list[Document] = self.__question_repository.get_question_documents(question.question)
                    documents_str = "\n".join([document.content for document in documents])
                    Logger.info("the question is retrieved_successfully", "ANSWER")
                    prompt: str = self.__build_prompt(question.question, documents_str)
                    generator_pipeline: TextGenerationPipeline = pipeline(
                        "text-generation",
                        model="Qwen/Qwen3-0.6B",
                        device=Accelerator().device
                    )
                    generated_answer = self._generate(prompt, generator_pipeline)
                    question_answer: QuestionAnswer = QuestionAnswer(question=_question, answer=generated_answer)
                    self.__question_repository.create_question_answer(question_answer)
                else:
                    generated_answer = cache_question_answer.answer
        return generated_answer

    # def answer_dataset(self, student_search_results:

    def __build_prompt(self, question: str, retrieved_documents: str) -> str:
        return (
            PROMPT .replace("{RETRIEVED_DOCUMENTS}", retrieved_documents)
           .replace("{USER_QUESTION}", question)
        )

    def _generate(self, prompt: str, pipeline: TextGenerationPipeline) -> str:
        results: str = pipeline(prompt, max_new_tokens=100)[0]["generated_text"]
        return results

answer_manager: AnswerManager = AnswerManager(
        search_engine=search_engine,
        question_repository=question_repository,
        config_manager=config_manager
)

__all__ = [
    "answer_manager",
    "AnswerManager"
]
