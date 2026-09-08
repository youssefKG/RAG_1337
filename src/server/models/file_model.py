from typing import cast
from django.db.models import Model, CharField, FloatField, AutoField
from typing_extensions import override


class FileModel(Model):
    id: int = AutoField(primary_key=True)
    path: str = CharField(unique=True)
    last_modified_at: float = FloatField()

    @override
    def __str__(self) -> str:
        return f"{self.path} {self.last_modified_at} {cast(int, self.pk)}"
