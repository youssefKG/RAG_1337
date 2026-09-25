from ..collection import MyCollection
from chromadb import Collection
from src.server.entities import DocumentInterface
from dataclasses import dataclass, asdict 




@dataclass
class DocumentCollectionMettadata:
    file_id: int
    file_path: str
    doc_length: int


@dataclass
class DocumentsCollection:
    ids: list[int] = list()
    documents: list[str] = list()
    metadata: list[dict[str, int | str]] = list()


class DocumentCollection(MyCollection):
    def __init__(self) -> None:
        super().__init__()
        self.__collection: Collection = self._client.get_or_create_collection(name="document")


    def file_by_id(self, id: int) -> None:
        pass


    def create_many(self, documents: list[DocumentInterface]) -> None:
        documents_collection: DocumentsCollection = self.__get_documents_collection(documents)
        self.__collection.add(**asdict(documents_collection))

    def get_by_ids(self) -> None:
        pass


    def __get_documents_collection(self, documents: list[DocumentInterface]) -> DocumentsCollection:
        documents_collection: DocumentsCollection = DocumentsCollection()
        for doc in documents:
            documents_collection.ids.append(doc.id)
            documents_collection.documents.append(doc.content if doc.content else "")
            documents_collection.metadata.append(asdict(DocumentCollectionMettadata(file_id=doc.file.id, file_path=doc.file.path, doc_length=doc.length)))
        return documents_collection
