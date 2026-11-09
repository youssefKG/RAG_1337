
"""Define the interface for vector-based document repositories."""

from typing import Protocol
from src.core.entities import Document


class VectorDocumentRepositoryInterface(Protocol):
    """Specify operations supported by vector document repositories.

    Implementations provide document storage, deletion, and similarity-based
    retrieval through a vector database.
    """

    def create_many(self, documents: list[Document]) -> None:
        """Store multiple documents in the vector database.

        Args:
            documents: Documents to store.
        """
        ...

    def delete_all(self) -> None:
        """Delete all documents from the vector database."""
        ...

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete all documents associated with a file.

        Args:
            file_id: Identifier of the file whose documents are deleted.
        """
        ...

    def get_documents_ids_search(
        self, query: str, top_k: int
    ) -> list[str]:
        """Retrieve document identifiers using vector similarity.

        Args:
            query: Text query used to search for similar documents.
            top_k: Maximum number of document identifiers to retrieve.

        Returns:
            Identifiers of the most relevant documents.
        """
        ...


__all__ = ["VectorDocumentRepositoryInterface"]
