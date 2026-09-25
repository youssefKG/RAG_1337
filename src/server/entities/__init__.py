from typing import Protocol


class FileInterface(Protocol):
    id: int
    path: str
    last_modified_at: float


class DocumentInterface(Protocol):
    """document interface"""
    id: int
    start_index: int
    end_index: int
    length: int
    file: FileInterface
    content: str | None


class DocumentTermInterface(Protocol):
    id: int
    frequency: int
    value: str
    document: DocumentInterface


__all__ = [
    "DocumentInterface",
    "DocumentInterface",
    "FileInterface",
]
