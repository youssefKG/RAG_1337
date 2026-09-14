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
        # self.__invert_index: InvertIndex = defaultdict(list[Posting])
        self.__invert_index: InvertIndexType = defaultdict(list[PostingType])

    def __call__(self, query: str) -> InvertIndexType:
        new_terms: set[str] = set(query.split()) & set(self.__invert_index.keys())
        terms_documents: list[DocumentTermInterface] = (
            self.__document_term_repository.get_by_values(new_terms)
        )
        for term_doc in terms_documents:
            if term_doc not in self.__invert_index.keys():
                pass
        return self.__invert_index
