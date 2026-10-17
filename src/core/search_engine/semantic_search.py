from src.core.vector_repositories_interfaces import VectorDocumentRepositoryInterface
from src.core.entities import Document
class SemanticSearch:
    def __init__(self, vector_document_repository: VectorDocumentRepositoryInterface) -> None:
        self.__vector_document_repository: VectorDocumentRepositoryInterface = vector_document_repository

    def __call__(self) -> list[Document]:
        return list()
