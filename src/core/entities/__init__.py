from dataclasses import dataclass, field
import uuid

@dataclass(frozen=False)
class File:
    file_path: str
    last_modified_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass(frozen=False)
class Document:
    start_index: int
    end_index: int
    length: int
    file: File
    content: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass(frozen=False)
class Term:
    document: Document
    value: str
    frequency: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

__all__ =  ["File", "Document", "Term"]
