from typing import Literal
from pydantic import ValidationError
from src.core.utils import Logger
from src.core.entities import Document, QuestionAnswer, Question
from src.core.validation_models import MinimalSearchResults, StudentSearchResults
from src.core.config_manager import ConfigManager, config_manager

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
        config_manager: ConfigManager
    ) -> None:
        self.__config_manager: ConfigManager = config_manager

    def answer(self, question: str, top_k: int, is_hybrid: bool) -> str:
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
                from src.server.repositories import question_repository
                cache_question_answer: QuestionAnswer | None = question_repository.get_question_answer(question)
                is_cache_question_searching_strategy_changed: bool = True if cache_question_answer and cache_question_answer.question.search_type == "HYBRID" else False != is_hybrid
                if (
                    cache_question_answer is None 
                    or cache_question_answer.question.top_k != top_k
                    or is_hybrid != is_cache_question_searching_strategy_changed
                ):
                    from src.core.search_engine import search_engine, SearchType
                    from transformers import pipeline, TextGenerationPipeline
                    from accelerate import Accelerator
                    search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
                    Logger.warn("The question is not found in the cache. Running the retrieval", "ANSWER")
                    minimal_search_results: MinimalSearchResults = search_engine(
                        question=question,
                        top_k=top_k,
                        search_type=search_type
                   )
                    documents: list[Document] = question_repository.get_question_documents(question)
                    documents_str = "\n".join([document.content for document in documents])
                    Logger.info("the question is retrieved_successfully", "ANSWER")
                    prompt: str = self.__build_prompt(question, documents_str)
                    generator_pipeline: TextGenerationPipeline = pipeline(
                        "text-generation",
                        model="Qwen/Qwen3-0.6B",
                        device=Accelerator().device
                    )
                    generated_answer = generator_pipeline(prompt, max_new_tokens=100)[0]["generated_text"]
                    _question: Question = Question(
                        id=minimal_search_results.question_id,
                        question=question,
                        top_k=top_k,
                        search_type=search_type.name
                    )
                    question_answer: QuestionAnswer = QuestionAnswer(question=_question, answer=generated_answer)
                    question_repository.create_question_answer(question_answer)
                else:
                    Logger.info("The question answer is found in cache", "ANSWER")
                    generated_answer = cache_question_answer.answer
        return generated_answer
    

    def answer_dataset(self, student_search_results: str, save_directory: str, is_hybrid: bool) -> None:
        pass


    def __load_student_search_results(self, student_search_results_path: str) -> StudentSearchResults:
        student_search_results: StudentSearchResults
        with open(student_search_results_path, "r") as file:
            content: str = file.read()
            try:
                pass
            except ValidationError as error:
                pass

        return student_search_results



    def __build_prompt(self, question: str, retrieved_documents: str) -> str:
        return (
            PROMPT .replace("{RETRIEVED_DOCUMENTS}", retrieved_documents)
           .replace("{USER_QUESTION}", question)
        )


answer_manager: AnswerManager = AnswerManager(
        config_manager=config_manager
)

__all__ = [
    "answer_manager",
    "AnswerManager"
]
