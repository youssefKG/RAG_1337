from typing import cast

from django.db import DatabaseError

from src.server.models import (
    QuestionModel,
    QuestionAnswerModel,
    QuestionDocumentModel,
)
from src.server.errors import CustomDatabaseError
from src.core.entities import (
    Question,
    QuestionDocument,
    QuestionAnswer,
    Document,
)


class QuestionRepository:
    def __init__(self) -> None:
        self.__question_model: type[QuestionModel] = QuestionModel
        self.__question_answer_model: type[QuestionAnswerModel] = (
            QuestionAnswerModel
        )
        self.__question_document_model: type[QuestionDocumentModel] = (
            QuestionDocumentModel
        )

    def create_question(self, question: Question) -> None:
        try:
            _ = self.__question_model.objects.create(
                id=question.id,
                question=question.question,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create question with ID '{question.id}'."
            ) from error

    def get(self, question: str) -> Question | None:
        try:
            question_model: QuestionModel | None = (
                self.__question_model.objects.filter(question=question).first()
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve question from the database."
            ) from error

        return cast(Question | None, question_model)

    def delete(self, question: str) -> None:
        try:
            _ = self.__question_model.objects.filter(
                question=question
            ).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete question from the database."
            ) from error

    def create(self, question: Question) -> None:
        try:
            _ = self.__question_model.objects.create(
                id=question.id,
                top_k=question.top_k,
                search_type=question.search_type,
                question=question.question,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create question with ID '{question.id}'."
            ) from error

    def get_question_answer(self, question: str) -> QuestionAnswer | None:
        try:
            question_answer_model: QuestionAnswerModel | None = (
                self.__question_answer_model.objects.filter(
                    question__question=question
                ).first()
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve the answer associated with the question."
            ) from error

        return cast(QuestionAnswer | None, question_answer_model)

    def create_many_question_document(
        self,
        question_documents: list[QuestionDocument],
    ) -> None:
        question_document_models: list[QuestionDocumentModel] = [
            QuestionDocumentModel(
                id=question_doc.id,
                question_id=question_doc.question.id,
                document_id=question_doc.document.id,
            )
            for question_doc in question_documents
        ]

        try:
            _ = self.__question_document_model.objects.bulk_create(
                question_document_models,
                batch_size=400,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create {len(question_documents)}"
                + " question-document associations."
            ) from error

    def get_question_documents(
        self,
        question: str,
    ) -> list[Document]:
        try:
            question_documents: list[QuestionDocument] = cast(
                list[QuestionDocument],
                list(
                    self.__question_document_model.objects.filter(
                        question__question=question
                    )
                ),
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve documents associated with the question."
            ) from error

        return [question_doc.document for question_doc in question_documents]

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        try:
            _ = self.__question_answer_model.objects.create(
                id=question_answer.id,
                question_id=question_answer.question.id,
                answer=question_answer.answer,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to create answer for question ID"
                + f" '{question_answer.question.id}'."
            ) from error

    def delete_all(self) -> None:
        try:
            _ = self.__question_model.objects.all().delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete all questions from the database."
            ) from error

    def create_many_questions_answers(
        self,
        questions_answers: list[QuestionAnswer],
    ) -> None:
        questions_answers_models: list[QuestionAnswerModel] = [
            QuestionAnswerModel(
                id=question_answer.id,
                question_id=question_answer.question.id,
                answer=question_answer.answer,
            )
            for question_answer in questions_answers
        ]

        try:
            _ = self.__question_answer_model.objects.bulk_create(
                questions_answers_models,
                batch_size=100,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create {len(questions_answers)} question answers."
            ) from error
