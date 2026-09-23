from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    PositiveIntegerField,
    AutoField,
)
from .file_model import FileModel


class DocumentModel(Model):
    id: int = AutoField(primary_key=True)
    file: ForeignKey[FileModel] = ForeignKey(FileModel, on_delete=CASCADE)
    start_index: int = PositiveIntegerField()
    end_index: int = PositiveIntegerField()
    length: int = PositiveIntegerField()
