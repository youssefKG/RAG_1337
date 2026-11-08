"""Database model linking questions to relevant documents."""

from django.db.models import Model, CharField, ForeignKey, CASCADE
from .question_model import QuestionModel
from .document_model import DocumentModel
from typing import cast


class QuestionDocumentModel(Model):
    """Represent the association between a question and a document.

    Attributes:
        id: Unique identifier of the question-document association.
        question: Question associated with the document.
        document: Document associated with the question.
    """

    id: str = cast(str, cast(object, CharField(primary_key=True)))
    question: QuestionModel = cast(
        QuestionModel,
        cast(object, ForeignKey(to=QuestionModel, on_delete=CASCADE)),
    )
    document: DocumentModel = cast(
        DocumentModel,
        cast(object, ForeignKey(to=DocumentModel, on_delete=CASCADE)),
    )
