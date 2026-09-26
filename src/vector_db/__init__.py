from chromadb.api import ClientAPI
from chromadb import HttpClient
from .collections import  VectorDocumentRepository


client: ClientAPI = HttpClient(host='localhost', port=8000)


vector_document_repository: VectorDocumentRepository = VectorDocumentRepository(client)

__all__= ["vector_document_repository"]
