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

    def __call__(self, query: str) -> InvertIndexType:
        new_terms: set[str] = set(query.split()) - set(self.__invert_index.keys())
        terms_documents: list[DocumentTermInterface] = (
            self.__document_term_repository.get_by_values(new_terms)
        )
        for term in new_terms:
            if term not in self.__invert_index.keys():
                self.__invert_index[term].extend(
                    self.__get_term_documents(terms_documents, term)
                )
        return self.__invert_index

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

    def __set_idf_terms(self, query_term: list[str]) -> None:
        self.__idf_terms = dict()
        for term in query_terms:
            number_of_document_contain_term: int = len(self.__invert_index[term])
            nominator: float = (
                self.__total_number_of_documents - number_of_document_contain_term + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            self.__terms_idfs[term] = math.log(nominator / dominator)
