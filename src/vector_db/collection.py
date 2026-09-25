from chromadb.api import ClientAPI
from chromadb import HttpClient

client: ClientAPI = HttpClient(host='localhost', port=8000)

class MyCollection:
    def __init__(self) -> None:
        self._client: ClientAPI = client
