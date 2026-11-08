"""Define the database model for document terms."""

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
    """Represent a term and its frequency within a document.

    Attributes:
        id: Unique identifier of the document-term record.
        frequency: Number of occurrences of the term in the document.
        value: Text value of the term.
        document: Document associated with the term.
    """

    id: str = cast(str, cast(object, CharField(primary_key=True)))
    frequency: int = cast(int, cast(object, PositiveIntegerField()))
    value: str = cast(str, cast(object, CharField()))
    document: ForeignKey[DocumentModel] = ForeignKey(
        DocumentModel, on_delete=CASCADE
    )

    class Meta:
        """Define constraints for document-term records."""

        constraints = [
            UniqueConstraint(
                fields=["value", "document_id"], name="unicite_produit_version"
            )
        ]
