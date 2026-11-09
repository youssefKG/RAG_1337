"""Provides database operations for document term entities."""

from typing import cast

from django.db import DatabaseError

from src.server.repositories.document_repository import DocumentRepository
from src.server.models import DocumentTermModel
from src.server.errors import CustomDatabaseError
from src.core.entities import Term


class TermRepository:
    """Manage document term persistence and retrieval operations."""

    def __init__(
        self,
        *,
        document_repository: DocumentRepository,
    ) -> None:
        """Initialize the term repository.

        Args:
            document_repository: Repository
            responsible for document operations.
        """
        self.__model: type[DocumentTermModel] = DocumentTermModel
        self.__all_terms = self.__model.objects.all()

    def get_by_terms_values(self, values: set[str]) -> list[Term]:
        """Retrieve document terms matching the provided values.

        Related documents are loaded alongside their associated terms.

        Args:
            values: Set of term values used to filter document terms.

        Returns:
            List of matching term entities.

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        try:
            document_term_models: list[DocumentTermModel] = list(
                self.__all_terms.filter(value__in=values).select_related(
                    "document"
                )
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to retrieve terms matching the provided values."
            ) from error

        return cast(list[Term], document_term_models)

    @property
    def count(self) -> int:
        """Return the total number of stored document terms.

        Returns:
            Number of document terms in the database.

        Raises:
            CustomDatabaseError: If the database count operation fails.
        """
        try:
            return self.__model.objects.all().count()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to count document terms in the database."
            ) from error

    def create_many(
        self,
        terms_documents: list[Term],
    ) -> None:
        """Persist multiple document terms using bulk database insertion.

        Args:
            terms_documents: List of term entities containing their values,
                frequencies, document references, and identifiers.

        Raises:
            CustomDatabaseError: If the bulk insertion fails.
        """
        documents_terms_model: list[DocumentTermModel] = [
            DocumentTermModel(
                frequency=term.frequency,
                value=term.value,
                document_id=term.document.id,
                id=term.id,
            )
            for term in terms_documents
        ]

        try:
            _: list[DocumentTermModel] = self.__model.objects.bulk_create(
                documents_terms_model,
                batch_size=50000,
            )
        except DatabaseError as error:
            raise CustomDatabaseError(
                f"Failed to create {len(terms_documents)}"
                + " document terms in the database."
            ) from error

    def delete_all(self) -> None:
        """Delete all document terms from the database.

        Raises:
            CustomDatabaseError: If the database deletion fails.
        """
        try:
            _ = self.__model.objects.all().delete()
        except DatabaseError as error:
            raise CustomDatabaseError(
                "Failed to delete all document terms from the database."
            ) from error
