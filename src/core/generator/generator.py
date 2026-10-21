from core.search_engine import SearchEngine
from src.core.indexer import Indexer
from src.server.repositories import QuestionRepositoryInterface


Prompt: str = """
You are a helpful enterprise assistant. Answer the user's question using only the context provided below. Do not assume or extrapolate. If the answer is not present in the context, state "I cannot answer this based on the provided information."
Context:
{retrieved_documents}
Question:
{user_question}
Instructions:
Think step-by-step before answering. Cite the specific source document name or ID for each key claim.
"""

class Generator:
    def __init__(self, search_engine: SearchEngine, indexer: Indexer, question_repository: QuestionRepositoryInterface) -> None:
        self.__search_engine: SearchEngine = search_engine
        self.__question_repository: QuestionRepositoryInterface = question_repository
