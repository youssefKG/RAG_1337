from django.db.models import CharField, Model, IntegerField
from typing import cast


class QuestionModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    question: str = cast(str, cast(object, CharField()))
    tok_k: int = cast(int, cast(object, IntegerField()))
