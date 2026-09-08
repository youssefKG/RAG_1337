from typing import Protocol


class FileInterface(Protocol):
    id: int
    path: str
    last_modified_at: float


class DocumentInterface(Protocol):
    id: int
    start_index: int
    end_index: int
    length: int
    file: FileInterface


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
