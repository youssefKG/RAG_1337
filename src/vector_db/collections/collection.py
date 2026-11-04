from chromadb.api import ClientAPI


class MyCollection:
    def __init__(self, client: ClientAPI) -> None:
        self._client: ClientAPI = client
