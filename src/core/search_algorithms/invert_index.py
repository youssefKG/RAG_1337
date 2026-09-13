from typing import Callable

from src.server.repositories import (
    DocumentRepository,
    DocumentTermRepository,
)
from collections import defaultdict
from .types import InvertIndexType, PostingType


class InvertIndex:
    def __init__(
        self,
        /,
        *,
        document_term_repository: DocumentTermRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self.__document_term_repository: DocumentTermRepository = (
            document_term_repository
        )
        self.__document_repository: DocumentRepository = document_repository
        # self.__invert_index: InvertIndex = defaultdict(list[Posting])
        self.__invert_index: InvertIndexType = defaultdict(list[PostingType])

    def __call__(self, query: str) -> InvertIndexType:
        new_terms: set[str] = set(query.split()) & set(self.__invert_index.keys())
        for term in new_terms:
            pass
        return self.__invert_index
