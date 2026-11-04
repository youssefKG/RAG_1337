from typing import Annotated, cast
from django.db import DatabaseError

from src.core.entities import File
from src.server.errors import CustomDatabaseError
from src.server.models import FileModel


class FileRepository:
    def __init__(self) -> None:
        self.__model: type[FileModel] = FileModel

    def create(self, file: File) -> File:
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
        try:
            return self.__model.objects.all().count()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to count files in the database."
            ) from error

    def get_or_create_by_path(
        self, file: File
    ) -> tuple[File, Annotated[bool, "is created"]]:
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
        try:
            _ = self.__model.objects.filter(path=path).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to delete file with path '{path}'."
            ) from error

    def delete_by_id(self, file_id: str) -> None:
        try:
            _ = self.__model.objects.filter(id=file_id).delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to delete file with ID '{file_id}'."
            ) from error

    def get_by_path(self, path: str) -> File | None:
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
        try:
            file_models: list[FileModel] = list(self.__model.objects.all())
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve all files from the database."
            ) from error

        return cast(list[File], file_models)

    def delete_all(self) -> None:
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
