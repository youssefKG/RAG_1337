from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    PositiveIntegerField,
    CharField
)
from .file_model import FileModel
from typing import cast


class DocumentModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    file: ForeignKey[FileModel] = ForeignKey(FileModel, on_delete=CASCADE)
    start_index: int = cast(int, cast(object, PositiveIntegerField()))
    end_index: int = cast(int, cast(object, PositiveIntegerField()))
    content: str = cast(str, cast(object, CharField()))
    length: int = cast(int, cast(object, PositiveIntegerField()))
