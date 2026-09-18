from src.server.repositories import (
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)
from collections import defaultdict

from typing import TypeAlias, Annotated
from src.server.entities import DocumentInterface, DocumentTermInterface

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
        document_repository: DocumentRepositoryInterface,
    ) -> None:
        self.__document_term_repository: DocumentTermRepositoryInterface = (
            document_term_repository
        )
        self.__document_repository: DocumentRepositoryInterface = document_repository
        self.__invert_index: InvertIndexType = defaultdict(PostingType)
        self.total_number_of_documents: int = self.__document_repository.count
        self.avg_document_length: int = (
            self.__document_repository.get_avg_document_length
        )

    def __call__(self, query_terms: list[str]) -> list[DocumentInterface]:
        # add new terms to invert index from user query
        new_terms: set[str] = set(query_terms) - set(self.__invert_index.keys())
        if len(new_terms) != 0:
            terms_documents: list[DocumentTermInterface] = (
                self.__document_term_repository.get_by_terms_values(new_terms)
            )
            self.__add_new_terms_to_invert_index(terms_documents, new_terms)
        return self.__document_repository.get_by_terms_values(set(query_terms))

    def __add_new_terms_to_invert_index(
        self, terms_documents: list[DocumentTermInterface], new_terms: set[str]
    ) -> None:
        for new_term_value in new_terms:
            for doc_term in terms_documents:
                if doc_term.value == new_term_value:
                    self.__invert_index[new_term_value][doc_term.document.id] = (
                        doc_term.document,
                        doc_term.frequency,
                    )

    @property
    def invert_index(self) -> InvertIndexType:
        return self.__invert_index
