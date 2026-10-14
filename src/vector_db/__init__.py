from chromadb.api import ClientAPI
from chromadb import HttpClient
from .collections import  VectorDocumentRepository

client: ClientAPI = HttpClient(
        host='localhost',
        port=8000,
        # settings=Settings(allow_reset=True, anonymized_telemetry=False)
)


# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
vector_document_repository: VectorDocumentRepository = VectorDocumentRepository(client)

__all__= ["vector_document_repository"]
