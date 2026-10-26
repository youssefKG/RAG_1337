from enum import Enum, auto
from typing import Protocol
from collections import defaultdict
from typing import TypeAlias, Annotated
from src.core.entities import Document

PostingType: TypeAlias = tuple[Annotated[int, "term frequency"], Document]
InvertIndexType: TypeAlias = defaultdict[
    Annotated[str, "term value"], list[PostingType]
]


class SearchMethod(Protocol):
    def __call__(
        self,
        question: str,
        top_k: int
    ) -> list[Document]: ...

class SearchType(Enum):
    LEXICAL = auto()
    HYBRID = auto()
