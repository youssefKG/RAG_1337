from typing import Annotated, cast

from src.server.repositories.document_repository import DocumentRepository

from src.server.models import DocumentTermModel
from src.server.entities import DocumentTermInterface


class DocumentTermRepository:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
    ) -> None:
        self.__model: type[DocumentTermModel] = DocumentTermModel
        self.__all_terms = self.__model.objects.all()

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
        _ = self.__model.objects.filter(id=document_term_id).delete()

    # TEST:
    def get_by_documet_id(self, document_id: int) -> list[DocumentTermInterface]:
        terms_models: list[DocumentTermModel] = list(
            self.__model.objects.filter(document_id=document_id)
        )
        return cast(list[DocumentTermInterface], terms_models)

    def all(self) -> list[DocumentTermInterface]:
        return [
            cast(DocumentTermInterface, cast(object, document_term))
            for document_term in self.__all_terms
        ]

    def get_by_values(self, values: set[str]) -> list[DocumentTermInterface]:
        document_term_models: list[DocumentTermModel] = list(
            self.__all_terms.filter(value__in=values).select_related("document")
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
        documents_terms_model: list[DocumentTermModel] = [
            DocumentTermModel(
                frequency=term_frequency, value=term_value, document_id=document_id
            )
            for term_frequency, term_value, document_id in terms_documents
        ]
        _: list[DocumentTermModel] = self.__model.objects.bulk_create(
            documents_terms_model, batch_size=20000
        )

    def get_document_term_value_and_document_id(
        self, document_id: int, term_value: str
    ) -> DocumentTermInterface | None:
        document_term_model: DocumentTermModel | None = self.__model.objects.filter(
            document_id=document_id, value=term_value
        ).first()

        return cast(DocumentTermInterface | None, cast(object, document_term_model))
