from typing import Protocol
from src.core.entities import DocumentInterface

class VectorDocumentRepositoryInterface(Protocol):
    def create_many(self, documents: list[DocumentInterface]) -> None:
        pass

__all__ =  ["VectorDocumentRepositoryInterface"]
