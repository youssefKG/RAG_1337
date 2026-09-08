from django.db.models import (
    CASCADE,
    AutoField,
    CharField,
    Model,
    PositiveIntegerField,
    ForeignKey,
    UniqueConstraint,
)

from .document_model import DocumentModel


class DocumentTermModel(Model):
    id: int = AutoField(primary_key=True)
    frequency: int = PositiveIntegerField()
    value: str = CharField()
    document: ForeignKey[DocumentModel] = ForeignKey(DocumentModel, on_delete=CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["value", "document_id"], name="unicite_produit_version"
            )
        ]
