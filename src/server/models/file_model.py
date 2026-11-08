"""Database model representing a file indexed by the RAG system."""

from typing import cast
from django.db.models import Model, CharField, FloatField


class FileModel(Model):
    """Store metadata about a file indexed by the RAG system.

    Attributes:
        id: Unique identifier of the file.
        path: Unique filesystem path identifying the file.
        last_modified_at: Timestamp of the file's last modification.
    """

    id: str = cast(str, cast(object, CharField(primary_key=True)))
    path: str = cast(str, cast(object, CharField(unique=True)))
    last_modified_at: float = cast(float, cast(object, FloatField()))
