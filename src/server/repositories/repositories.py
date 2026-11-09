"""Defines repository protocols for data
persistence and retrieval."""

from typing import Annotated, Protocol
from src.core.entities import (
    Term,
    Document,
    File,
    Question,
    QuestionDocument,
    QuestionAnswer,
)


class FileRepositoryInterface(Protocol):
    """Define the contract for file persistence
    and retrieval operations."""

    def create(self, file: File) -> File:
        """Persist a file and return the created file entity."""
        ...

    def delete_by_path(self, path: str) -> None:
        """Delete a file identified by its path."""
        ...

    def delete_by_id(self, file_id: str) -> None:
        """Delete a file identified by its unique identifier."""
        ...

    def get_by_path(self, path: str) -> File | None:
        """Retrieve a file by its path,
        returning None if it does not exist."""
        ...

    def create_many(self, files: list[File]) -> None:
        """Persist multiple file entities."""
        ...

    def get_or_create_by_path(
        self, file: File
    ) -> tuple[File, Annotated[bool, "is created"]]:
        """Retrieve a file by path or create it if it does not exist.

        Returns:
            A tuple containing the file entity and a boolean indicating
            whether the file was created.
        """
        ...

    def update(
        self,
        /,
        *,
        id: str,
        path: str | None = None,
        last_modified_at: float | None = None,
    ) -> None:
        """Update the attributes of an existing file.

        Args:
            id: Identifier of the file to update.
            path: New file path, if provided.
            last_modified_at: New modification timestamp, if provided.
        """
        ...

    @property
    def count(self) -> int:
        """Return the total number of stored files."""
        ...

    def delete_all(self) -> None:
        """Delete all stored files."""
        ...

    def delete_by_files_paths(self, files_paths: set[str]) -> None:
        """Delete by files paths

        Args:
            files_paths: Path of the file to retrieve.

        Returns: None

        Raises:
            CustomDatabaseError: If the database query fails.
        """
        ...


class DocumentRepositoryInterface(Protocol):
    """Define the contract for document persistence
    and retrieval operations."""

    def create_many(
        self,
        documents: list[Document],
    ) -> None:
        """Persist multiple document entities."""
        ...

    @property
    def get_avg_document_length(self) -> float:
        """Return the average length of stored documents."""
        ...

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete all documents associated with a specific file."""
        ...

    @property
    def count(self) -> int:
        """Return the total number of stored documents."""
        ...

    def all(self) -> list[Document]:
        """Retrieve all stored documents."""
        ...

    def delete_all(self) -> None:
        """Delete all stored documents."""
        ...

    def get_by_ids(self, ids: list[str]) -> list[Document]:
        """Retrieve documents matching the provided identifiers."""
        ...

    def get_by_terms_values(self, values: set[str]) -> list[Document]:
        """Retrieve documents matching the provided term values."""
        ...


class TermRepositoryInterface(Protocol):
    """Define the contract for term persistence and retrieval operations."""

    def create_many(
        self,
        terms_documents: list[Term],
    ) -> None:
        """Persist multiple term entities."""
        ...

    def get_by_terms_values(self, values: set[str]) -> list[Term]:
        """Retrieve terms matching the provided values."""
        ...

    def delete_all(self) -> None:
        """Delete all stored terms."""
        ...

    @property
    def count(self) -> int:
        """Return the total number of stored terms."""
        ...


class QuestionRepositoryInterface(Protocol):
    """Define the contract for question, answer,
    and document association operations."""

    def get(self, question: str) -> Question | None:
        """Retrieve a question by its content."""
        ...

    def create(self, question: Question) -> None:
        """Persist a question entity."""
        ...

    def get_question_documents(self, question: str) -> list[Document]:
        """Retrieve all documents associated with a question."""
        ...

    def delete(self, question: str) -> None:
        """Delete a question identified by its content."""
        ...

    def create_many_question_document(
        self, question_documents: list[QuestionDocument]
    ) -> None:
        """Persist multiple question-document associations."""
        ...

    def delete_all(self) -> None:
        """Delete all stored questions."""
        ...

    def get_question_answer(self, question: str) -> QuestionAnswer | None:
        """Retrieve the answer associated with a question."""
        ...

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        """Persist an answer associated with a question."""
        ...

    def create_many_questions_answers(
        self, questions_answers: list[QuestionAnswer]
    ) -> None:
        """Persist multiple question-answer associations."""
        ...
