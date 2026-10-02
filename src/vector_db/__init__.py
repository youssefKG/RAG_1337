from chromadb.api import ClientAPI
from chromadb import HttpClient
from chromadb.config import Settings
from .collections import  VectorDocumentRepository
# from sentence_transformers import SentenceTransformer

client: ClientAPI = HttpClient(
        host='localhost',
        port=8000,
        # settings=Settings(allow_reset=True, anonymized_telemetry=False)
)


# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
vector_document_repository: VectorDocumentRepository = VectorDocumentRepository(client)

__all__= ["vector_document_repository"]
