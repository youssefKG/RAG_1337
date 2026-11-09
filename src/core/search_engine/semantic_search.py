"""Provide semantic document retrieval capabilities.

This module implements semantic search by retrieving relevant document
identifiers from a vector repository and resolving them into document
entities through the document repository.

It provides a unified interface for retrieving documents using
vector-based similarity search.
"""

from src.core.vector_repositories_interfaces import (
    VectorDocumentRepositoryInterface,
)
from src.server.repositories import DocumentRepositoryInterface
from src.core.entities import Document
from src.vector_db import vector_document_repository
from src.server.repositories import document_repository


class SemanticSearch:
    """Retrieve relevant documents using semantic similarity search."""

    def __init__(
        self,
        vector_document_repository: VectorDocumentRepositoryInterface,
        document_repository: DocumentRepositoryInterface,
    ) -> None:
        """Initialize semantic search with its repository dependencies.

        Args:
            vector_document_repository: Repository responsible for
                retrieving document identifiers through vector similarity.
            document_repository: Repository responsible for retrieving
                document entities by their identifiers.
        """
        self.__vector_document_repository: (
            VectorDocumentRepositoryInterface
        ) = vector_document_repository
        self.__document_repository: DocumentRepositoryInterface = (
            document_repository
        )

    def __call__(self, question: str, top_k: int) -> list[Document]:
        """Retrieve documents semantically related to a question.

        Args:
            question: Natural language query used for semantic retrieval.
            top_k: Maximum number of document identifiers to retrieve.

        Returns:
            Documents corresponding to the retrieved identifiers.
        """
        documents_ids: list[str] = (
            self.__vector_document_repository.get_documents_ids_search(
                question, top_k
            )
        )
        documents: list[Document] = self.__document_repository.get_by_ids(
            documents_ids
        )
        return documents


semantic_search = SemanticSearch(
    vector_document_repository,
    document_repository
)
