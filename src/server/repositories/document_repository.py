from typing import cast, Annotated
from src.server.repositories.file_repository import FileRepository
from src.server.models import DocumentModel
from src.core.entities import Document
from django.db import transaction
from django.db.models import Avg, QuerySet


class DocumentRepository:
    def __init__(self, file_repository: FileRepository) -> None:
        self.__model: type[DocumentModel] = DocumentModel
        self.__file_repository: FileRepository = FileRepository()

    def get_by_terms_values(self, values: set[str]) -> list[Document]:
        documents_models: list[DocumentModel] = list(
            self.__model.objects.filter(documenttermmodel__value__in=values).distinct()
        )
        return cast(list[Document], documents_models)

    def all(self) -> list[Document]:
        return cast(list[Document], list(self.__model.objects.all()))

    @property
    def count(self) -> int:
        return self.__model.objects.all().count()

    def delete_by_file_id(self, file_id: str) -> None:
        _ = self.__model.objects.filter(file__id=file_id).delete()

    def create_many(
        self,
        documents: list[Document],
    ) -> None:
        with transaction.atomic():
            documents_models_to_create: list[DocumentModel] = [
                DocumentModel(
                    id = doc.id,
                    start_index=doc.start_index,
                    end_index=doc.end_index,
                    file_id=doc.file.id,
                    length=doc.length,
                )
                for doc in documents
            ]
            _: list[DocumentModel] = self.__model.objects.bulk_create(
                documents_models_to_create, batch_size=10000
            )

    def delete_all(self) -> None:
        _ = self.__model.objects.all().delete()

    @property
    def get_avg_document_length(self) -> float:
        avg_dl = self.__model.objects.aggregate(Avg("length", default=0))
        return cast(float, avg_dl["length__avg"])
