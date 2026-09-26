from typing import cast, Annotated
from src.server.repositories.file_repository import FileRepository
from src.server.models import DocumentModel
from src.core.entities import DocumentInterface
from django.db import transaction
from django.db.models import Avg, QuerySet


class DocumentRepository:
    def __init__(self, file_repository: FileRepository) -> None:
        self.__model: type[DocumentModel] = DocumentModel
        self.__file_repository: FileRepository = FileRepository()
        self.__all_documents: QuerySet[DocumentModel, DocumentModel] = (
            self.__model.objects.all()
        )

    def get_by_terms_values(self, values: set[str]) -> list[DocumentInterface]:
        documents_models: list[DocumentModel] = list(
            self.__all_documents.filter(documenttermmodel__value__in=values).distinct()
        )
        return cast(list[DocumentInterface], documents_models)

    def all(self) -> list[DocumentInterface]:
        return cast(list[DocumentInterface], list(self.__model.objects.all()))

    @property
    def count(self) -> int:
        return self.__model.objects.all().count()

    def delete_by_file_id(self, file_id: int) -> None:
        _ = self.__model.objects.filter(file__id=file_id).delete()

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

    @property
    def get_avg_document_length(self) -> float:
        avg_dl = self.__model.objects.aggregate(Avg("length", default=0))
        return cast(float, avg_dl["length__avg"])
