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
        self.total_number_of_documents: int = self.__document_repository.count
        self.avg_document_length: int = (
            self.__document_repository.get_avg_document_length
        )

    def __call__(self, query_terms: set[str]) -> list[DocumentInterface]:
        new_terms: set[str] = query_terms - set(self.__invert_index.keys())
        terms_documents: list[DocumentTermInterface] = (
            self.__document_term_repository.get_by_terms_values(new_terms)
        )
        for term in new_terms:
            if term not in self.__invert_index.keys():
                self.__invert_index[term].extend(
                    self.__get_term_documents(terms_documents, term)
                )
        # TODO: test this with conditates documents from db if is slow try take document conditates from the invert invert index
        conditates_documents: list[DocumentInterface] = self.__get_condidates_documents(
            query_terms
        )
        return conditates_documents

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
        condidates_documents: dict[int, tuple[DocumentInterface, int]] = dict()
        for term in query_terms:
            postings: list[PostingType] = self.__invert_index[term]
            for frequency, doc in postings:
                if doc.id in condidates_documents.keys():
                    condidates_documents[doc.id] = (
                        doc,
                        condidates_documents[doc.id][1] + frequency,
                    )
                else:
                    condidates_documents[doc.id] = (
                        doc,
                        frequency,
                    )
        condidate = list(condidates_documents.values())
        condidate.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in condidate][:100]
