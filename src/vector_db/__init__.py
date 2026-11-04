from chromadb.api import ClientAPI
from chromadb import PersistentClient

from .collections import VectorDocumentRepository

client: ClientAPI = PersistentClient(path="./data/processed/vector_db/")

vector_document_repository: VectorDocumentRepository = (
    VectorDocumentRepository(client)
)

__all__ = ["vector_document_repository"]
