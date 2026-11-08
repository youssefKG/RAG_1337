
"""Define validation models used throughout the RAG pipeline.

Provides schemas for questions, retrieved sources, search results,
generated answers, and RAG datasets.
"""

import uuid
from pydantic import BaseModel, Field
from typing import List


class MinimalSource(BaseModel):
    """Represent a retrieved source within a document.

    Attributes:
        file_path: Path of the file containing the source.
        first_character_index: Starting character position.
        last_character_index: Ending character position.
    """

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Represent a question without a generated answer.

    Attributes:
        question_id: Unique identifier generated automatically.
        question: Text of the question.
    """

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Represent a question with its answer and supporting sources.

    Attributes:
        sources: Sources used to generate the answer.
        answer: Generated answer associated with the question.
    """

    sources: list[MinimalSource]
    answer: str


class MinimalSearchResults(BaseModel):
    """Represent the essential results of a search operation.

    Attributes:
        question_id: Identifier of the associated question.
        question: Original question submitted for retrieval.
        retrieved_sources: Sources returned by the search operation.
    """

    question_id: str
    question: str
    retrieved_sources: list[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Represent search results enriched with a generated answer.

    Attributes:
        answer: Generated answer associated with the search results.
    """

    answer: str


class RagDataset(BaseModel):
    """Represent a dataset containing answered and unanswered questions.

    Attributes:
        rag_questions: Collection of questions with optional answers
            and supporting sources.
    """

    rag_questions: list[AnsweredQuestion | UnansweredQuestion]


class StudentSearchResults(BaseModel):
    """Represent search results submitted by a student.

    Attributes:
        search_results: Search results for the submitted questions.
        k: Number of documents requested per question.
    """

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """Represent student search results with generated answers.

    Attributes:
        search_results: Search results enriched with generated answers.
        k: Number of documents requested per question.
    """

    search_results: List[MinimalAnswer]
    k: int


__all__ = [
    "UnansweredQuestion",
    "RagDataset",
    "StudentSearchResults",
    "MinimalSource",
    "MinimalSearchResults",
    "MinimalAnswer",
    "StudentSearchResultsAndAnswer",
]

