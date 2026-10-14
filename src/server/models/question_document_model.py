from django.db.models import Model, CharField, ForeignKey, CASCADE
from .question_model import QuestionModel
from .document_model import DocumentModel
from typing import cast

class QuestionDocumentModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    query: QuestionModel = cast(QuestionModel, cast(object, ForeignKey(to=QuestionModel, on_delete=CASCADE)))
    document: DocumentModel = cast(DocumentModel, cast(object, ForeignKey(to=DocumentModel, on_delete=CASCADE)))
