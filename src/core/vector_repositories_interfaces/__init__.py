from typing import Protocol
from src.core.entities import Document

class VectorDocumentRepositoryInterface(Protocol):
    def create_many(self, documents: list[Document]) -> None:
        ...

    def delete_all(self) -> None:
        ...

    def delete_by_file_id(self, file_id: str) -> None:
        ...


__all__ =  ["VectorDocumentRepositoryInterface"]
