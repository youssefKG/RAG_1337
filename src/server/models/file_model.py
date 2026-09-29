from typing import cast
from django.db.models import Model, CharField, FloatField


class FileModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    path: str = cast(str, cast(object, CharField(unique=True)))
    last_modified_at: float = cast(float, cast(object, FloatField()))
