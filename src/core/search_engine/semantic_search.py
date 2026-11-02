from src.core.vector_repositories_interfaces import (
    VectorDocumentRepositoryInterface,
)
from src.server.repositories import DocumentRepositoryInterface
from src.core.entities import Document
from src.vector_db import vector_document_repository
from src.server.repositories import document_repository


class SemanticSearch:
    def __init__(
        self,
        vector_document_repository: VectorDocumentRepositoryInterface,
        document_repository: DocumentRepositoryInterface,
    ) -> None:
        self.__vector_document_repository: (
            VectorDocumentRepositoryInterface
        ) = vector_document_repository
        self.__document_repository: DocumentRepositoryInterface = (
            document_repository
        )

    def __call__(self, question: str, top_k: int) -> list[Document]:
        documents_ids: list[str] = (
            self.__vector_document_repository.get_documents_ids_search(
                question, top_k
            )
        )
        documents: list[Document] = (
            self.__document_repository.get_by_ids(documents_ids)
        )
        return documents


semantic_search = SemanticSearch(
    vector_document_repository, document_repository
)
