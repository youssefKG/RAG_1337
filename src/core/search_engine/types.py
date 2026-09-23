from typing import Protocol
from collections import defaultdict
from typing import TypeAlias, Annotated
from src.server.entities import DocumentInterface

PostingType: TypeAlias = tuple[Annotated[int, "term frequency"], DocumentInterface]
InvertIndexType: TypeAlias = defaultdict[
    Annotated[str, "term value"], list[PostingType]
]


class SearchMethod(Protocol):
    def __call__(
        self, query_terms: list[str], top_k: int
    ) -> list[DocumentInterface]: ...
