from typing import cast
from src.server.models import QuestionModel, QuestionAnswerModel, QuestionDocumentModel

from src.core.entities import Question, QuestionDocument, Document, QuestionAnswer

class QuestionRepository:
    def __init__(self) -> None:
        self.__question_model: type[QuestionModel] = QuestionModel
        self.__question_answer_model: type[QuestionAnswerModel] = QuestionAnswerModel
        self.__question_document_model: type[QuestionDocumentModel] = QuestionDocumentModel

    def create_question(self, question: Question) -> None:
        _ = self.__question_model.objects.create(id=question.id, question=question.question)

    def get_question_documents(self, question_id: str) -> list[QuestionDocument]:
        question_documents_models: list[QuestionDocumentModel] = list(self.__question_document_model.objects.filter(question__id=question_id))
        return cast(list[QuestionDocument], question_documents_models)

    def get_question_answer(self, question_id: str) -> QuestionAnswer | None:
        question_answer_model: QuestionAnswerModel | None = self.__question_answer_model.objects.filter(question__id=question_id).first()
        return cast(QuestionAnswer | None, question_answer_model)

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        pass

    def get_question(self, question_id: str) -> None | Question:
        pass
