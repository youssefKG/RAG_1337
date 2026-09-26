from typing import TypeAlias, Annotated
from src.server.repositories import (
    DocumentTermRepositoryInterface,
)
from collections import defaultdict

from src.core.entities import DocumentInterface, DocumentTermInterface

PostingType: TypeAlias = dict[
    Annotated[int, "document id"],
    tuple[DocumentInterface, Annotated[int, "term frequency"]],
]
InvertIndexType: TypeAlias = defaultdict[Annotated[str, "term value"], PostingType]


class InvertIndex:
    def __init__(
        self,
        /,
        *,
        document_term_repository: DocumentTermRepositoryInterface,
    ) -> None:
        self.__document_term_repository: DocumentTermRepositoryInterface = (
            document_term_repository
        )
        self.__invert_index: InvertIndexType = defaultdict(PostingType)

    def __call__(self, query_terms: list[str]) -> None:
        # add new terms to invert index from user query
        new_terms: set[str] = set(query_terms) - set(self.__invert_index)
        if new_terms:
            terms_documents: list[DocumentTermInterface] = (
                self.__document_term_repository.get_by_terms_values(new_terms)
            )
            self.__add_new_terms_to_invert_index(terms_documents)

    def __add_new_terms_to_invert_index(
        self, terms_documents: list[DocumentTermInterface]
    ) -> None:
        for doc_term in terms_documents:
            self.__invert_index[doc_term.value][doc_term.document.id] = (
                doc_term.document,
                doc_term.frequency,
            )

    @property
    def invert_index(self) -> InvertIndexType:
        return self.__invert_index
