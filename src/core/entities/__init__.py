from dataclasses import dataclass, field
import uuid

@dataclass(frozen=False)
class File:
    file_path: str
    last_modified_at: float
    id: str

@dataclass(frozen=False)
class Document:
    id: str
    start_index: int
    end_index: int
    length: int
    file: File
    content: str | None = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass(frozen=False)
class Term:
    document: Document
    value: str
    frequency: int
    id: str

__all__ = [
    "File",
    "Document",
    "Term"
]
