"""Repository for storing and retrieving documents using ChromaDB."""

from typing import cast
from dataclasses import dataclass, asdict, field

from chromadb import Collection
from chromadb.api import ClientAPI

from .collection import MyCollection
from src.core.entities import Document


@dataclass(frozen=False)
class DocumentCollectionMettadata:
    """Store metadata associated with a document in a ChromaDB collection.

    Attributes:
        file_id: Unique identifier of the source file.
        file_path: Filesystem path of the source file.
        doc_length: Length of the document content.
        first_character_index: Starting character position in the source file.
        last_character_index: Ending character position in the source file.
    """

    file_id: str
    file_path: str
    doc_length: str
    first_character_index: int
    last_character_index: int


@dataclass(frozen=False)
class DocumentsCollection:
    """Group document data into the structure expected by ChromaDB.

    Attributes:
        ids: Unique identifiers of the documents.
        documents: Text contents of the documents.
        metadatas: Metadata dictionaries associated with each document.
    """

    ids: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    metadatas: list[dict[str, str | int]] = field(default_factory=list)


class VectorDocumentRepository(MyCollection):
    """Manage document storage and retrieval through a ChromaDB collection.

    This repository provides operations for adding documents, retrieving
    relevant document IDs through vector similarity search, and deleting
    documents by their source file or from the entire collection.
    """

    def __init__(self, client: ClientAPI) -> None:
        """Initialize the repository and retrieve or create its collection.

        Args:
            client: ChromaDB client used to access the collection.
        """
        super().__init__(client)
        self.__collection: Collection = self._client.get_or_create_collection(
            name="document"
        )

    def create_many(self, documents: list[Document]) -> None:
        """Add multiple documents to the ChromaDB collection.

        Documents are converted into parallel ID, content, and metadata
        collections before being inserted.

        Args:
            documents: Documents to add to the collection.
        """
        documents_collection: DocumentsCollection = (
            self.__get_documents_collection(documents)
        )
        if documents_collection.ids:
            self.__collection.add(
                ids=documents_collection.ids,
                documents=documents_collection.documents,
                metadatas=documents_collection.metadatas,
            )

    def get_documents_ids_search(self, query: str, top_k: int) -> list[str]:
        """Retrieve document IDs matching a query through similarity search.

        Args:
            query: Text query used to find relevant documents.
            top_k: Maximum number of results to retrieve.

        Returns:
            IDs of the documents ranked by similarity to the query.
        """
        result = self.__collection.query(query_texts=[query], n_results=top_k)[
            "ids"
        ][0]
        return cast(list[str], cast(object, result))

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete all documents associated with a specific source file.

        Args:
            file_id: Unique identifier of the source file.
        """
        _ = self.__collection.delete(where={"file_id": file_id})

    def __get_documents_collection(
        self, documents: list[Document]
    ) -> DocumentsCollection:
        """Convert domain documents into ChromaDB-compatible collections.

        Args:
            documents: Domain documents to convert.

        Returns:
            A collection containing document IDs, contents, and metadata.
        """
        documents_collection: DocumentsCollection = DocumentsCollection()
        for doc in documents:
            documents_collection.ids.append(doc.id)
            documents_collection.documents.append(
                doc.content if doc.content else ""
            )
            documents_collection.metadatas.append(
                asdict(
                    DocumentCollectionMettadata(
                        file_id=doc.file.id,
                        file_path=doc.file.path,
                        doc_length=str(doc.length),
                        first_character_index=doc.start_index,
                        last_character_index=doc.end_index,
                    )
                )
            )
        return documents_collection

    def delete_all(self) -> None:
        """Delete every document stored in the ChromaDB collection."""
        all_ids: list[str] = self.__collection.get()["ids"]
        if all_ids:
            _ = self.__collection.delete(ids=all_ids)
