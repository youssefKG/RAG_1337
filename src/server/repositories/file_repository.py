"""Provides database operations for file entities."""

from typing import Annotated, cast
from django.db import DatabaseError

from src.core.entities import File
from src.server.errors import CustomDatabaseError
from src.server.models import FileModel


class FileRepository:
    """Manage file persistence and retrieval operations."""

    def __init__(self) -> None:
        """Initialize the file repository."""
        self.__model: type[FileModel] = FileModel

    def create(self, file: File) -> File:
        """Create and persist a file in the database.

        Args:
            file: File entity containing the data to persist.

        Returns:
            The created file entity.

        Raises:
            CustomDatabaseError: If the database creation fails.
        """
        try:
            created_file: FileModel = self.__model.objects.create(
                path=file.path,
                last_modified_at=file.last_modified_at,
                id=file.id,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create file with path '{file.path}'."
            ) from error

        return cast(File, cast(object, created_file))

    @property
    def count(self) -> int:
        """Return the total number of stored files.

        Returns:
            Number of files in the database.

        Raises:
            CustomDatabaseError: If the database count operation fails.
        """
        try:
            return self.__model.objects.all().count()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to count files in the database."
            ) from error

    def get_or_create_by_path(
        self, file: File
    ) -> tuple[File, Annotated[bool, "is created"]]:
        """Retrieve an existing file by path or create it if absent.

        Args:
            file: File entity containing the path and default values.

        Returns:
            A tuple containing the retrieved or created file and a boolean
            indicating whether a new file was created.

        Raises:
            CustomDatabaseError: If the database operation fails.
        """
        try:
            file_model, is_created = self.__model.objects.get_or_create(
                path=file.path,
                defaults={
                    "last_modified_at": file.last_modified_at,
                    "id": file.id,
                },
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to retrieve or create file with path '{file.path}'."
            ) from error
        return (cast(File, cast(object, file_model)), is_created)

    def create_many(self, files: list[File]) -> None:
        """Persist multiple files using bulk database insertion.

        Args:
            files: List of file entities to insert into the database.

        Raises:
            CustomDatabaseError: If the bulk insertion fails.
        """
        try:
            files_to_create: list[FileModel] = [
                FileModel(
                    path=file.path,
                    last_modified_at=file.last_modified_at,
                    id=file.id,
                )
                for file in files
            ]
            _ = self.__model.objects.bulk_create(
                files_to_create, batch_size=1000
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create {len(files)} files in the database."
            ) from error

    def delete_by_path(self, path: str) -> None:
        """Delete a file identified by its path.

        Args:
            path: Path of the file to delete.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.filter(path=path).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to delete file with path '{path}'."
            ) from error

    def delete_by_id(self, file_id: str) -> None:
        """Delete a file identified by its ID.

        Args:
            file_id: Identifier of the file to delete.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.filter(id=file_id).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to delete file with ID '{file_id}'."
            ) from error


    def delete_by_files_paths(self, files_paths: set[str]) -> None:
        """Delete by files paths

        Args:
            files_paths: Path of the file to retrieve.

        Returns: None

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            _ = self.__model.objects.filter(path__in=files_paths).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete files with path {files_paths"
            ) from error


    def get_by_path(self, path: str) -> File | None:
        """Retrieve a file by its path.

        Args:
            path: Path of the file to retrieve.

        Returns:
            The matching file entity, or None if no file is found.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            file_model: FileModel | None = self.__model.objects.filter(
                path=path
            ).first()
            if file_model is None:
                return None

            return cast(File, cast(object, file_model))
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to retrieve file with path '{path}'."
            ) from error

    def all(self) -> list[File]:
        """Retrieve all files stored in the database.

        Returns:
            List containing all stored file entities.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            file_models: list[FileModel] = list(self.__model.objects.all())
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve all files from the database."
            ) from error

        return cast(list[File], file_models)

    def delete_all(self) -> None:
        """Delete all files from the database.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.all().delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete all files from the database."
            ) from error

    def update(
        self,
        /,
        *,
        id: str,
        path: str | None = None,
        last_modified_at: float | None = None,
    ) -> None:
        """Update the attributes of an existing file.

        Args:
            id: Identifier of the file to update.
            path: New file path, if provided.
            last_modified_at: New modification timestamp, if provided.

        Raises:
            CustomDatabaseError: If the database update fails.
        """
        try:
            file_model: FileModel | None = self.__model.objects.filter(
                id=id
            ).first()
            if file_model is None:
                # TODO: handle the case where no file is found
                return

            if path is not None:
                file_model.path = path

            if last_modified_at is not None:
                file_model.last_modified_at = last_modified_at

            file_model.save()
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to update file with ID '{id}'."
            ) from error
