"""Provide an in-memory inverted index for lexical document retrieval.

This module implements an inverted index that maps term values to the
documents containing them, along with their corresponding term frequencies.

It retrieves previously indexed terms from the term repository and
maintains their document associations in memory for search operations.
"""

from typing import TypeAlias, Annotated
from src.server.repositories import (
    TermRepositoryInterface,
    term_repository,
)
from collections import defaultdict

from src.core.entities import Document, Term


PostingType: TypeAlias = dict[
    Annotated[str, "document id"],
    tuple[Document, Annotated[int, "term frequency"]],
]


InvertIndexType: TypeAlias = defaultdict[
        Annotated[str, "term value"], PostingType
]


class InvertIndexError(Exception):
    ...


class InvertIndex:
    """Manage an in-memory inverted index of terms and documents."""

    def __init__(
        self,
        /,
        *,
        term_repository: TermRepositoryInterface,
    ) -> None:
        """Initialize the inverted index.

        Args:
            term_repository: Repository responsible for retrieving
                indexed terms and their associated documents.
        """
        self.__term_repository: TermRepositoryInterface = term_repository
        self.__invert_index: InvertIndexType = defaultdict(PostingType)

    def __call__(self, query_terms: list[str]) -> None:
        """Load missing query terms into the in-memory inverted index.

        Identifies terms that are not already indexed in memory, retrieves
        their document associations from the term repository, and adds
        them to the inverted index.

        Args:
            query_terms: Terms extracted from the search query.
        """
        # add new terms to invert index from user query
        new_terms: set[str] = set(query_terms) - set(self.__invert_index)
        if new_terms:
            terms_documents: list[Term] = (
                self.__term_repository.get_by_terms_values(new_terms)
            )
            self.__add_new_terms_to_invert_index(terms_documents)

    def __add_new_terms_to_invert_index(
        self, terms_documents: list[Term]
    ) -> None:
        """Add term-document associations to the inverted index.

        Args:
            terms_documents: Terms containing their associated documents
                and occurrence frequencies.
        """
        for doc_term in terms_documents:
            self.__invert_index[doc_term.value][doc_term.document.id] = (
                doc_term.document,
                doc_term.frequency,
            )

    @property
    def invert_index(self) -> InvertIndexType:
        """Return the current in-memory inverted index.

        Returns:
            The mapping of term values to their document postings.
        """
        return self.__invert_index


invert_index: InvertIndex = InvertIndex(
    term_repository=term_repository
)
