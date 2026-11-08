"""Define search-related types, protocols, and strategies."""

from enum import Enum, auto
from typing import Protocol
from collections import defaultdict
from typing import TypeAlias, Annotated
from src.core.entities import Document


PostingType: TypeAlias = tuple[Annotated[int, "term frequency"], Document]
"""
Represent an inverted-index
posting containing term frequency and its document.
"""

InvertIndexType: TypeAlias = defaultdict[
    Annotated[str, "term value"], list[PostingType]
]
"""Represent an inverted index mapping terms to their document postings."""


class SearchMethod(Protocol):
    """Define the interface required by document search implementations."""

    def __call__(self, question: str, top_k: int) -> list[Document]:
        """Search for documents relevant to a question.

        Args:
            question: Search query.
            top_k: Maximum number of documents to retrieve.

        Returns:
            Documents ranked by their relevance to the question.
        """
        ...


class SearchType(Enum):
    """Represent the available document retrieval strategies."""

    LEXICAL = auto()
    """Retrieve documents using lexical search."""

    HYBRID = auto()
    """Retrieve documents using a combination of search strategies."""
