from typing import Annotated, cast
from src.core.entities import File

from src.server.models import FileModel


class FileRepository:
    def __init__(self) -> None:
        self.__model: type[FileModel] = FileModel

    def create(self, file: File) -> File:
        created_file: FileModel = self.__model.objects.create(
            path=file.path, last_modified_at=file.last_modified_at, id=file.id
        )
        return cast(File, cast(object, created_file))

    @property
    def count(self) -> int:
        return self.__model.objects.all().count()

    def get_or_create_by_path( self, file: File) -> tuple[File, Annotated[bool, "is created"]]:
        file_model, is_created = self.__model.objects.get_or_create(
            path=file.path,
            defaults={
                "last_modified_at": file.last_modified_at,
                "id": file.id
            }
        )
        return (cast(File, cast(object, file_model)), is_created)

    def create_many(self, files: list[File]) -> None:
        files_to_create: list[FileModel] = [
            FileModel(
                path=file.path,
                last_modified_at=file.last_modified_at,
                id=file.id
            ) for file in files
        ]
        _ = self.__model.objects.bulk_create(files_to_create, batch_size=1000)


    def delete_by_path(self, path: str) -> None:
        _ = self.__model.objects.filter(path=path).delete()

    def delete_by_id(self, file_id: str) -> None:
        _ = self.__model.objects.filter(id=file_id).delete()

    def get_by_path(self, path: str) -> File | None:
        file_model: FileModel | None = self.__model.objects.filter(path=path).first()
        if file_model is None:
            return None
        return cast(File, cast(object, file_model))

    def all(self) -> list[File]:
        file_models: list[FileModel] = list(self.__model.objects.all())
        return cast(list[File], file_models)


    def delete_all(self) -> None:
        _ = self.__model.objects.all().delete()

    def update(
        self,
        /,
        *,
        id: str,
        path: str | None = None,
        last_modified_at: float | None = None,
    ) -> None:
        file_model: FileModel | None = self.__model.objects.filter(id=id).first()
        if file_model is None:
            # TODO: handle the case where no file found
            return
        if path is not None:
            file_model.path = path
        if last_modified_at is not None:
            file_model.last_modified_at = last_modified_at
        file_model.save()
