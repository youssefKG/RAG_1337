from src.core.vector_repositories_interfaces import VectorDocumentRepositoryInterface
from src.core.entities import Document

class SemanticSearch:
    def __init__(self, vector_document_repository: VectorDocumentRepositoryInterface) -> None:
        self.__vector_document_repository: VectorDocumentRepositoryInterface = vector_document_repository

    def __call__(self, question: str, top_k: int) -> list[Document]:
        vector_documents = self.__vector_document_repository.search(question, top_k)
        print(vector_documents)
        return list()
