import sys
from .collection import MyCollection
from chromadb import Collection
from src.core.entities import DocumentInterface
from chromadb.api import ClientAPI
from dataclasses import dataclass, asdict , field


@dataclass(frozen=False)
class DocumentCollectionMettadata:
    file_id: int
    file_path: str
    doc_length: int


@dataclass(frozen=False)
class DocumentsCollection:
    ids: list[int] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    metadata: list[dict[str, int | str]] = field(default_factory=list)


class VectorDocumentRepository(MyCollection):
    def __init__(self, client: ClientAPI) -> None:
        super().__init__(client)
        self.__collection: Collection = self._client.get_or_create_collection(name="document")


    def file_by_id(self, id: int) -> None:
        pass


    def create_many(self, documents: list[DocumentInterface]) -> None:
        documents_collection: DocumentsCollection = self.__get_documents_collection(documents)
        self.__collection.add(ids=[str(id) for id in documents_collection.ids])

    def get_by_ids(self) -> None:
        pass


    def get_cosin_simalitry_documents(self, query: str, top_k: int) -> None:
        result = self.__collection.query(query_texts=[query], n_results=top_k)
        pass

    def __get_documents_collection(self, documents: list[DocumentInterface]) -> DocumentsCollection:
        documents_collection: DocumentsCollection = DocumentsCollection()
        for doc in documents:
            documents_collection.ids.append(doc.id)
            documents_collection.documents.append(doc.content if doc.content else "")
            documents_collection.metadata.append(
                asdict(
                    DocumentCollectionMettadata(
                        file_id=doc.file.id,
                        file_path=doc.file.path,
                        doc_length=doc.length
                    )
                )
            )
        return documents_collection
