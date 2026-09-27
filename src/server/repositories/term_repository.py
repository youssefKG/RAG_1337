from typing import Annotated, cast

from src.server.repositories.document_repository import DocumentRepository

from src.server.models import DocumentTermModel
from src.core.entities import Term


class TermRepository:
    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
    ) -> None:
        self.__model: type[DocumentTermModel] = DocumentTermModel
        self.__all_terms = self.__model.objects.all()

    def get_by_terms_values(self, values: set[str]) -> list[Term]:
        document_term_models: list[DocumentTermModel] = list(
            self.__all_terms.filter(value__in=values).select_related("document")
        )
        return cast(list[Term], document_term_models)

    @property
    def count(self) -> int:
        return self.__model.objects.all().count()

    def create_many(
        self,
        terms_documents: list[Term],
    ) -> None:
        documents_terms_model: list[DocumentTermModel] = [
            DocumentTermModel(
                frequency=term.frequency,
                value=term.value,
                document_id=term.document.id,
                id=term.id
            ) for term in terms_documents
        ]
        _: list[DocumentTermModel] = self.__model.objects.bulk_create(
            documents_terms_model, batch_size=100000
        )

    def delete_all(self) -> None:
        _ = self.__model.objects.all().delete()
