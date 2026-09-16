from typing import cast, Annotated
from src.server.repositories.file_repository import FileRepository
from src.server.repositories.errors import DBNotFoundError
from src.server.models import DocumentModel, FileModel
from src.server.entities import DocumentInterface
from django.db import transaction
from django.db.models import Avg


class DocumentRepository:
    def __init__(self, file_repository: FileRepository) -> None:
        self.__model: type[DocumentModel] = DocumentModel
        self.__file_repository: FileRepository = FileRepository()

    def get_by_id(self, id: int) -> DocumentInterface | None:
        document_model: DocumentModel | None = DocumentModel.objects.filter(
            pk=id
        ).first()
        return cast(DocumentInterface | None, cast(object, document_model))

    def get_by_ids(self, ids: list[int]) -> list[DocumentInterface]:
        documents_models: list[DocumentModel] = list(
            self.__model.objects.filter(pk__in=ids)
        )
        return cast(list[DocumentInterface], documents_models)

    def get_has_terms(self, values: set[str]) -> list[DocumentInterface]:
        documents_models: list[DocumentModel] = list(
            self.__model.objects.filter(documenttermmodel__value_in=values)
        )
        return cast(list[DocumentInterface], documents_models)

    def create(
        self, *, start_index: int, end_index: int, file_id: int, document_length: int
    ) -> DocumentInterface:

        file: FileModel | None = self.__file_repository.get_model_by_id(file_id)
        if file is None:
            raise DBNotFoundError(
                "Database Error:\n" + f"file with id {file_id} not found"
            )
        else:
            document_model: DocumentModel = DocumentModel.objects.create(
                start_index=start_index,
                end_index=end_index,
                file=file,
                length=document_length,
            )
            document_model.save()
            return cast(DocumentInterface, cast(object, document_model))

    def get_documents_has_term_value(self, term_value: str) -> list[DocumentInterface]:
        documents_models: list[DocumentModel] = list(
            self.__model.objects.filter(documenttermmodel__value=term_value)
        )
        return cast(list[DocumentInterface], documents_models)

    def delete_by_id(self, document_id: int) -> None:
        _ = self.__model.objects.filter(pk=document_id).delete()

    @property
    def count(self) -> int:
        return self.__model.objects.all().count()

    def delete_by_file_id(self, file_id: int) -> None:
        file: FileModel | None = self.__file_repository.get_model_by_id(file_id)
        if file is None:
            return
        _ = self.__model.objects.filter(file=file).delete()

    def get_model_by_id(self, document_id: int) -> DocumentModel | None:
        return self.__model.objects.filter(pk=document_id).first()

    def create_many(
        self,
        documents: list[
            tuple[
                Annotated[int, "start index"],
                Annotated[int, "end index"],
                Annotated[int, "document length"],
                Annotated[int, "file id"],
            ]
        ],
    ) -> list[DocumentInterface]:
        with transaction.atomic():
            documents_models_to_create: list[DocumentModel] = [
                DocumentModel(
                    start_index=start_index,
                    end_index=end_index,
                    file_id=file_id,
                    length=length,
                )
                for start_index, end_index, length, file_id in documents
            ]
            documents_models: list[DocumentModel] = self.__model.objects.bulk_create(
                documents_models_to_create
            )
            return cast(list[DocumentInterface], documents_models)

    def all(self) -> list[DocumentInterface]:
        documents_models: list[DocumentModel] = list(self.__model.objects.all())
        return cast(list[DocumentInterface], documents_models)

    @property
    def get_avg_document_length(self) -> int:
        avg_dl = self.__model.objects.aggregate(Avg("length", default=0))
        return cast(int, avg_dl["length__avg"])
