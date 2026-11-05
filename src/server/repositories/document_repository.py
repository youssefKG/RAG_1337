"""Provides database operations for document entities."""

from typing import cast
from django.db import DatabaseError
from django.db.models import Avg

from src.server.repositories.file_repository import FileRepository
from src.server.models import DocumentModel
from src.server.errors import CustomDatabaseError
from src.core.entities import Document


class DocumentRepository:
    """Manage document persistence and retrieval operations."""

    def __init__(self, file_repository: FileRepository) -> None:
        """Initialize the document repository.

        Args:
            file_repository: Repository responsible for file operations.
        """
        self.__model: type[DocumentModel] = DocumentModel
        self.__file_repository: FileRepository = FileRepository()

    def get_by_terms_values(self, values: set[str]) -> list[Document]:
        """Retrieve distinct documents matching the provided term values.

        Args:
            values: Set of term values used to identify matching documents.

        Returns:
            List of distinct documents matching at least one provided term.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            documents_models: list[DocumentModel] = list(
                self.__model.objects.filter(
                    documenttermmodel__value__in=values
                ).distinct()
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve documents matching the provided terms."
            ) from error

        return cast(list[Document], documents_models)

    def all(self) -> list[Document]:
        """Retrieve all documents stored in the database.

        Returns:
            List containing all stored documents.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            return cast(list[Document], list(self.__model.objects.all()))
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve all documents from the database."
            ) from error

    @property
    def count(self) -> int:
        """Return the total number of stored documents.

        Returns:
            Number of documents in the database.

        Raises:
            CustomDatabaseError: If the database count operation fails.
        """
        try:
            return self.__model.objects.all().count()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to count documents in the database."
            ) from error

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete all documents associated with a specific file.

        Args:
            file_id: Identifier of the file whose documents will be deleted.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.filter(file__id=file_id).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete documents associated with file ID:"
                + f" '{file_id}'."
            ) from error

    def create_many(
        self,
        documents: list[Document],
    ) -> None:
        """Persist multiple documents using bulk database insertion.

        Args:
            documents: Documents to be inserted into the database.

        Raises:
            CustomDatabaseError: If the bulk insertion fails.
        """
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
                documents_models_to_create, batch_size=10000
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create {len(documents)} documents in the database."
            ) from error

    def delete_all(self) -> None:
        """Delete all documents from the database.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.all().delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete all documents from the database."
            ) from error

    @property
    def get_avg_document_length(self) -> float:
        """Calculate the average length of all stored documents.

        Returns:
            Average document length, or zero if no documents exist.

        Raises:
            CustomDatabaseError: If the database aggregation fails.
        """
        try:
            avg_dl = self.__model.objects.aggregate(Avg("length", default=0))
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to calculate the average document length."
            ) from error

        return cast(float, avg_dl["length__avg"])

    def get_by_ids(self, ids: list[str]) -> list[Document]:
        """Retrieve documents matching the provided identifiers.

        Args:
            ids: List of document identifiers to retrieve.

        Returns:
            List of documents matching the provided identifiers.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            documents: list[Document] = cast(
                list[Document], list(self.__model.objects.filter(id__in=ids))
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve documents by their IDs."
            ) from error
        return documents
