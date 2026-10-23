from typing import Literal
from core.search_engine import SearchEngine, SearchType
from src.core.indexer import Indexer
from src.server.repositories import QuestionRepositoryInterface
from src.core.entities import  Question, Document, QuestionAnswer
from src.core.validation_models import UnansweredQuestion, AnsweredQuestion, MinimalSearchResults
from src.core.config_manager import ConfigManager
from transformers import pipeline, TextGenerationPipeline

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
        self.__pipeline: TextGenerationPipeline = pipeline("text-generation")
        self.__config_manager: ConfigManager = config_manager

    def answer(self, question: UnansweredQuestion, top_k: int, is_hybrid: bool) -> str:
        preindexing_strategy: Literal["lexical", "hybrid", "none"] = self.__config_manager.config.indexing_strategy
        generated_answer: str
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
                    search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
                    _ = self.__search_engine(
                            question=question,
                            top_k=top_k,
                            search_type=search_type
                    )
                    documents: list[Document] = self.__question_repository.get_question_documents(question.question)
                    documents_str = "\n".join([document.content for document in documents])
                    prompt: str = self.__build_prompt(question.question, documents_str)
                    generated_answer = self._generate(prompt)
                else:
                    generated_answer = cache_question_answer.answer
        return generated_answer

    # def answer_dataset(self, student_search_results:

    def __build_prompt(self, question: str, retrieved_documents: str) -> str:
        return (
            PROMPT .replace("{RETRIEVED_DOCUMENTS}", retrieved_documents)
           .replace("{USER_QUESTION}", question)
        )

    def _generate(self, prompt: str) -> str:
        results: str = self.__pipeline(prompt, max_length=200)[0]["generated_text"]
        return results
