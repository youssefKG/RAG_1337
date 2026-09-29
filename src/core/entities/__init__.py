from dataclasses import dataclass, field
from src.core.search_engine import SearchType
import uuid

@dataclass(frozen=False)
class File:
    path: str
    last_modified_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass(frozen=False)
class Document:
    start_index: int
    end_index: int
    length: int
    file: File
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass(frozen=False)
class Term:
    document: Document
    value: str
    frequency: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=False)
class Config:
    is_indexing_hybrid: bool = False
    max_chunk_size: bool = False
    search_type: SearchType = SearchType.LEXICAL


__all__ =  ["File", "Document", "Term", "Config"]
