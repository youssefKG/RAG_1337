from typing import Annotated, cast
from src.core.entities import FileInterface

from src.server.models import FileModel


class FileRepository:
    def __init__(self) -> None:
        self.__model: type[FileModel] = FileModel

    def create(self, *, path: str, last_modified_at: float) -> FileInterface:
        created_file: FileModel = self.__model.objects.create(
            path=path, last_modified_at=last_modified_at
        )
        return cast(FileInterface, cast(object, created_file))

    def get_or_create_by_path(
        self, *, path: str, last_modified_at: float
    ) -> tuple[FileInterface, Annotated[bool, "is created"]]:
        file_model, is_created = self.__model.objects.get_or_create(
            path=path, defaults={"last_modified_at": last_modified_at}
        )
        return (cast(FileInterface, cast(object, file_model)), is_created)

    def delete_by_path(self, path: str) -> None:
        _ = self.__model.objects.filter(path=path).delete()

    def delete_by_id(self, file_id: int) -> None:
        _ = self.__model.objects.filter(id=file_id).delete()

    def get_by_path(self, path: str) -> FileInterface | None:
        file_model: FileModel | None = self.__model.objects.filter(path=path).first()
        if file_model is None:
            return None
        return cast(FileInterface, cast(object, file_model))

    def all(self) -> list[FileInterface]:
        file_models: list[FileModel] = list(self.__model.objects.all())
        return cast(list[FileInterface], file_models)

    def update(
        self,
        /,
        *,
        id: int,
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
