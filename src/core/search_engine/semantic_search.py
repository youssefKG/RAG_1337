from typing import cast
from src.core.vector_repositories_interfaces import VectorDocumentRepositoryInterface
from src.server.repositories import DocumentRepositoryInterface
from src.core.entities import Document

class SemanticSearch:
    def __init__(
            self,
            vector_document_repository: VectorDocumentRepositoryInterface,
            document_repository: DocumentRepositoryInterface
    ) -> None:
        self.__vector_document_repository: VectorDocumentRepositoryInterface = vector_document_repository
        self.__document_repository: DocumentRepositoryInterface = document_repository

    def __call__(self, question: str, top_k: int) -> list[Document]:
        documents_ids: list[str] = self.__vector_document_repository.get_documents_ids_search(question, top_k)
        documents: list[Document] = self.__document_repository.get_by_ids(documents_ids)
        return documents
