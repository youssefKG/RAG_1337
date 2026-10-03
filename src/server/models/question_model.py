from django.db.models import CharField, Model
from typing import cast


class QuestionModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    query: str = cast(str, cast(object, CharField()))
