from typing import cast, Annotated
from src.server.models import QuestionModel, QuestionAnswerModel, QuestionDocumentModel
from src.core.validation_models import UnansweredQuestion

from src.core.entities import Question, QuestionDocument, QuestionAnswer, Document

class QuestionRepository:
    def __init__(self) -> None:
        self.__question_model: type[QuestionModel] = QuestionModel
        self.__question_answer_model: type[QuestionAnswerModel] = QuestionAnswerModel
        self.__question_document_model: type[QuestionDocumentModel] = QuestionDocumentModel

    def create_question(self, question: Question) -> None:
        _ = self.__question_model.objects.create(id=question.id, question=question.question)

    def get(self, question: str) -> Question | None:
        question_model: QuestionModel | None = self.__question_model.objects.filter(question=question).first()
        return cast(Question | None, question_model)

    def delete(self, question: str) -> None:
        _ = self.__question_model.objects.filter(question=question).delete()

    def create(self, question: Question) -> None:
        _ = self.__question_model.objects.create(**cast(dict[str, object], cast(object, question)))

    def get_question_answer(self, question_id: str) -> QuestionAnswer | None:
        question_answer_model: QuestionAnswerModel | None = self.__question_answer_model.objects.filter(question__id=question_id).first()
        return cast(QuestionAnswer | None, question_answer_model)

    def get_or_create_question(self, question: UnansweredQuestion) -> tuple[UnansweredQuestion, Annotated[bool, "is created"]]:
        _, is_created = self.__question_model.objects.get_or_create(id=question.question_id, question=question.question)
        return question, is_created

    def get_question_documents(self, question: str) -> list[Document]:
        question_documents: list[QuestionDocument] = cast(
                list[QuestionDocument],
                list(self.__question_document_model.objects.filter(document__question=question)))
        return [question_doc.document for question_doc in question_documents]
