from typing import cast
from django.db.models import (
    CASCADE,
    CharField,
    Model,
    PositiveIntegerField,
    ForeignKey,
    UniqueConstraint,
)

from .document_model import DocumentModel


class DocumentTermModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    frequency: int = cast(int, cast(object, PositiveIntegerField()))
    value: str = cast(str, cast(object, CharField()))
    document: ForeignKey[DocumentModel] = ForeignKey(DocumentModel, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["value", "document_id"], name="unicite_produit_version"
            )
        ]
