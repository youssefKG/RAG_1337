from typing import Annotated, cast

from src.server.repositories.document_repository import DocumentRepository

from src.server.models import DocumentTermModel
from src.server.entities import DocumentTermInterface
from django.db import transaction


class DocumentTermRepository:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
    ) -> None:
        self.__model: type[DocumentTermModel] = DocumentTermModel

    def create(
        self,
        *,
        term_frequency: int,
        term_value: str,
        document_id: int,
    ) -> DocumentTermInterface:
        document_term_model: DocumentTermModel = DocumentTermModel(
            frequency=term_frequency, value=term_value, document_id=document_id
        )
        document_term_model.save()
        return cast(DocumentTermInterface, cast(object, document_term_model))

    def delete_by_id(self, document_term_id: int) -> None:
        _ = self.__model.objects.filter(value=document_term_id).delete()

    # TEST:
    def get_by_documet_id(self, document_id: int) -> list[DocumentTermInterface]:
        terms_models: list[DocumentTermModel] = list(
            self.__model.objects.filter(document_id=document_id)
        )
        return cast(list[DocumentTermInterface], terms_models)

    def all(self) -> list[DocumentTermInterface]:
        return cast(list[DocumentTermInterface], list(self.__model.objects.all()))

    def get_by_values(self, values: list[str]) -> list[DocumentTermInterface]:
        document_term_models: list[DocumentTermModel] = list(
            self.__model.objects.filter(value__in=values)
        )

        return cast(list[DocumentTermInterface], document_term_models)

    def create_many(
        self,
        terms_documents: list[
            tuple[
                Annotated[int, "term frequency"],
                Annotated[str, "term value"],
                Annotated[int, "document id"],
            ]
        ],
    ) -> None:
        print(len(terms_documents))
        with transaction.atomic():
            print("start creating")
            documents_terms_model: list[DocumentTermModel] = [
                DocumentTermModel(
                    frequency=term_frequency, value=term_value, document_id=document_id
                )
                for term_frequency, term_value, document_id in terms_documents
            ]
            _: list[DocumentTermModel] = self.__model.objects.bulk_create(
                documents_terms_model, batch_size=10000
            )
