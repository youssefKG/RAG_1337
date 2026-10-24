from typing import cast
from src.server.models import QuestionModel, QuestionAnswerModel, QuestionDocumentModel
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
        _ = self.__question_model.objects.create(
            id=question.id,
            top_k=question.top_k,
            search_type=question.search_type,
            question=question.question
        )

    def get_question_answer(self, question: str) -> QuestionAnswer | None:
        question_answer_model: QuestionAnswerModel | None = self.__question_answer_model.objects.filter(
            question__question=question
        ).first()
        return cast(QuestionAnswer | None, question_answer_model)

    def create_many_question_document(self, question_documents: list[QuestionDocument]) -> None:
        question_document_models: list[QuestionDocumentModel] = [
            QuestionDocumentModel(
                id=question_doc.id,
                question_id=question_doc.question.id,
                document_id=question_doc.document.id,
            ) for question_doc in question_documents
        ]
        _ = self.__question_document_model.objects.bulk_create(question_document_models, batch_size=400)

    def get_question_documents(
            self,
            question: str,
    ) -> list[Document]:
        question_documents: list[QuestionDocument] = cast(
            list[QuestionDocument],
            list(
                self.__question_document_model.objects.filter(
                    question__question=question
                )
            )

        )
        return [question_doc.document for question_doc in question_documents]

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        _ = self.__question_answer_model.objects.create(
                id=question_answer.id,
                question_id=question_answer.question.id,
                answer=question_answer.answer
            )

    def delete_all(self) -> None:
        _ = self.__question_model.objects.all().delete()
