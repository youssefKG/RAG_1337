from collections import defaultdict
from typing import TypeAlias, Annotated
from src.server.entities import DocumentInterface

PostingType: TypeAlias = tuple[Annotated[int, "term frequency"], DocumentInterface]
InvertIndexType: TypeAlias = defaultdict[
    Annotated[str, "term value"], list[PostingType]
]
