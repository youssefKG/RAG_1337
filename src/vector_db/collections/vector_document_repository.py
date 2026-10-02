from .collection import MyCollection
from chromadb import Collection
from src.core.entities import Document 
from chromadb.api import ClientAPI
from dataclasses import dataclass, asdict , field


@dataclass(frozen=False)
class DocumentCollectionMettadata:
    file_id: str
    file_path: str
    doc_length: str


@dataclass(frozen=False)
class DocumentsCollection:
    ids: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    metadatas: list[dict[str, str]] = field(default_factory=list)


class VectorDocumentRepository(MyCollection):
    def __init__(self, client: ClientAPI) -> None:
        super().__init__(client)
        self.__collection: Collection = self._client.get_or_create_collection(name="document")


    def create_many(self, documents: list[Document]) -> None:
        documents_collection: DocumentsCollection = self.__get_documents_collection(documents)
        if documents_collection.ids:
            self.__collection.add(
                    ids=documents_collection.ids,
                    documents=documents_collection.documents,
                    metadatas=documents_collection.metadatas
            )

    def get_cosin_simalitry_documents(self, query: str, top_k: int) -> None:
        result = self.__collection.query(query_texts=[query], n_results=top_k)

    def delete_by_file_id(self, file_id: str) -> None:
        _ = self.__collection.delete(where={"file_id": file_id})

    def __get_documents_collection(self, documents: list[Document]) -> DocumentsCollection:
        documents_collection: DocumentsCollection = DocumentsCollection()
        for doc in documents:
            documents_collection.ids.append(doc.id)
            documents_collection.documents.append(doc.content if doc.content else "")
            documents_collection.metadatas.append(
                asdict(
                    DocumentCollectionMettadata(
                        file_id=doc.file.id,
                        file_path=doc.file.path,
                        doc_length=str(doc.length)
                    )
                )
            )
        return documents_collection

    def delete_all(self) -> None:
        all_ids: list[str]  = self.__collection.get()["ids"]
        if all_ids:
            _ = self.__collection.delete(ids=all_ids)



