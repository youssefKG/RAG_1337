"""Database model for storing answers associated with questions."""

from django.db.models import Model, CharField, ForeignKey, CASCADE
from typing import cast

from .question_model import QuestionModel


class QuestionAnswerModel(Model):
    """Represent an answer associated with a question.

    Attributes:
        id: Unique identifier of the question-answer record.
        question: Question to which the answer belongs.
        answer: Text content of the answer.
    """

    id: str = cast(str, cast(object, CharField(primary_key=True)))
    question: QuestionModel = cast(
        QuestionModel,
        cast(object, ForeignKey(to=QuestionModel, on_delete=CASCADE)),
    )
    answer: str = cast(str, cast(object, CharField()))
