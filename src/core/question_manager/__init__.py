from src.core.entities import Question, QuestionDocument, Document, QuestionAnswer
from src.server.repositories import QuestionRepositoryInterface
class QuestionManager:
    def __init__(self, question_repository: QuestionRepositoryInterface) -> None:
        self.__question_repository: QuestionRepositoryInterface = question_repository

    def create_question(self, question: Question) -> None:
        pass

    def get_question_documents(self, question_id: str) -> list[Document]:
        return []

    def get_question_answer(self, question_id: str) -> QuestionAnswer | None:
        return None

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        pass
