from src.server.repositories import (
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)
from collections import defaultdict

from typing import TypeAlias, Annotated
from src.server.entities import DocumentInterface, DocumentTermInterface

PostingType: TypeAlias = tuple[Annotated[int, "term frequency"], DocumentInterface]
InvertIndexType: TypeAlias = defaultdict[
    Annotated[str, "term value"], list[PostingType]
]


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
        self.__invert_index: InvertIndexType = defaultdict(list[PostingType])
        self.__idf_terms: dict[
            Annotated[str, "term value"], Annotated[int, "idf score"]
        ] = dict()
        self.total_number_of_documents: int = self.__document_repository.count
        self.avg_document_length: int = (
            self.__document_repository.get_avg_document_length
        )

    def __call__(
        self, query: str
    ) -> tuple[
        InvertIndexType, Annotated[list[DocumentInterface], "conditate documents"]
    ]:
        new_terms: set[str] = set(query.split()) - set(self.__invert_index.keys())
        terms_documents: list[DocumentTermInterface] = (
            self.__document_term_repository.get_by_values(new_terms)
        )
        for term in new_terms:
            if term not in self.__invert_index.keys():
                self.__invert_index[term].extend(
                    self.__get_term_documents(terms_documents, term)
                )
        # TODO: test this with conditates documents from db if is slow try take document conditates from the invert invert index
        conditates_documents: list[DocumentInterface] = self.__get_condidates_documents(
            set(query.split())
        )
        return self.__invert_index, conditates_documents

    def __get_term_documents(
        self, terms_documents: list[DocumentTermInterface], term_value: str
    ) -> list[PostingType]:
        return [
            (doc_term.frequency, doc_term.document)
            for doc_term in terms_documents
            if doc_term.value == term_value
        ]

    @property
    def invert_index(self) -> InvertIndexType:
        return self.__invert_index

    def __get_condidates_documents(
        self, query_terms: set[str]
    ) -> list[DocumentInterface]:
        conditates_documents: list[DocumentInterface] = (
            self.__document_repository.get_has_terms(query_terms)
        )
        return conditates_documents
