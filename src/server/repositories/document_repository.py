from typing import cast
from django.db import DatabaseError
from django.db.models import Avg

from src.server.repositories.file_repository import FileRepository
from src.server.models import DocumentModel
from src.server.errors import CustomDatabaseError
from src.core.entities import Document


class DocumentRepository:
    def __init__(self, file_repository: FileRepository) -> None:
        self.__model: type[DocumentModel] = DocumentModel
        self.__file_repository: FileRepository = FileRepository()

    def get_by_terms_values(self, values: set[str]) -> list[Document]:
        try:
            documents_models: list[DocumentModel] = list(
                self.__model.objects.filter(
                    documenttermmodel__value__in=values
                ).distinct()
            )
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to retrieve documents matching the provided terms.") from error

        return cast(list[Document], documents_models)

    def all(self) -> list[Document]:
        try:
            return cast(
                list[Document],
                list(self.__model.objects.all())
            )
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to retrieve all documents from the database.") from error

    @property
    def count(self) -> int:
        try:
            return self.__model.objects.all().count()
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to count documents in the database.") from error

    def delete_by_file_id(self, file_id: str) -> None:
        try:
            _ = self.__model.objects.filter(file__id=file_id).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(f"Failed to delete documents associated with file ID '{file_id}'.") from error

    def create_many(
        self,
        documents: list[Document],
    ) -> None:
        documents_models_to_create: list[DocumentModel] = [
            DocumentModel(
                id=doc.id,
                start_index=doc.start_index,
                end_index=doc.end_index,
                file_id=doc.file.id,
                length=doc.length,
                content=doc.content,
            )
            for doc in documents
        ]

        try:
            _: list[DocumentModel] = self.__model.objects.bulk_create(
                documents_models_to_create,
                batch_size=10000,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(f"Failed to create {len(documents)} documents in the database.") from error

    def delete_all(self) -> None:
        try:
            _ = self.__model.objects.all().delete()
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to delete all documents from the database.") from error

    @property
    def get_avg_document_length(self) -> float:
        try:
            avg_dl = self.__model.objects.aggregate(
                Avg("length", default=0)
            )
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to calculate the average document length.") from error

        return cast(float, avg_dl["length__avg"])

    def get_by_ids(self, ids: list[str]) -> list[Document]:
        try:
            documents: list[Document] = cast(
                list[Document],
                list(self.__model.objects.filter(id__in=ids))
            )
        except DatabaseError as error:
            raise CustomDatabaseError("Failed to retrieve documents by their IDs.") from error

        return documents
