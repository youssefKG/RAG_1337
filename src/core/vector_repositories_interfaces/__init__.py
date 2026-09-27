from typing import Protocol
from src.core.entities import Document

class VectorDocumentRepositoryInterface(Protocol):
    def create_many(self, documents: list[Document]) -> None:
        pass

__all__ =  ["VectorDocumentRepositoryInterface"]
