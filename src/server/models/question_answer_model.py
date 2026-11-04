from django.db.models import Model, CharField, ForeignKey, CASCADE
from .question_model import QuestionModel
from typing import cast


class QuestionAnswerModel(Model):
    id: str = cast(str, cast(object, CharField(primary_key=True)))
    question: QuestionModel = cast(
        QuestionModel,
        cast(object, ForeignKey(to=QuestionModel, on_delete=CASCADE)),
    )
    answer: str = cast(str, cast(object, CharField()))
