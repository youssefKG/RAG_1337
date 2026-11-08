"""Collection management utilities backed by ChromaDB."""

from chromadb.api import ClientAPI


class MyCollection:
    """Manage collections through a ChromaDB client.

    Attributes:
        _client: ChromaDB client used to interact with collections.
    """

    def __init__(self, client: ClientAPI) -> None:
        """Initialize the collection manager.

        Args:
            client: ChromaDB client used for collection operations.
        """
        self._client: ClientAPI = client
