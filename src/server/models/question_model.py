"""Database model for storing questions and their search configuration."""

from django.db.models import CharField, Model, IntegerField
from typing import cast


class QuestionModel(Model):
    """Represent a question submitted to the RAG system.

    Attributes:
        id: Unique identifier of the question.
        question: Text content of the submitted question.
        top_k: Maximum number of documents to retrieve for the question.
        search_type: Search strategy used to retrieve relevant documents.
    """

    id: str = cast(str, cast(object, CharField(primary_key=True)))
    question: str = cast(str, cast(object, CharField()))
    top_k: int = cast(int, cast(object, IntegerField()))
    search_type: str = cast(str, cast(object, CharField()))
