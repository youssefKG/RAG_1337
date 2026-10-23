from typing import Annotated, Protocol
from src.core.entities import (
    Term,
    Document,
    File,
    Question,
    QuestionDocument,
    QuestionAnswer
)


class FileRepositoryInterface(Protocol):
    def create(self, file: File) -> File: ...

    def delete_by_path(self, path: str) -> None: ...

    def delete_by_id(self, file_id: str) -> None: ...

    def get_by_path(self, path: str) -> File | None: ...

    def create_many(self, files: list[File]) -> None: ...

    def get_or_create_by_path(self, file: File) -> tuple[File, Annotated[bool, "is created"]]:
        ...

    def update(
        self,
        /,
        *,
        id: str,
        path: str | None = None,
        last_modified_at: float | None = None,
    ) -> None: ...

    @property
    def count(self) -> int: ...

    def delete_all(self) -> None: ...


class DocumentRepositoryInterface(Protocol):

    def create_many(
        self, documents: list[Document],
    ) -> None: ...

    @property
    def get_avg_document_length(self) -> float: ...

    def delete_by_file_id(self, file_id: str) -> None: ...

    @property
    def count(self) -> int: ...

    def get_by_terms_values(self, values: set[str]) -> list[Document]: ...

    def all(self) -> list[Document]:
        ...

    def delete_all(self) -> None: ...

    def get_by_ids(self, ids: list[str]) -> list[Document]:
        ...

class TermRepositoryInterface(Protocol):
    def create_many(
        self,
        terms_documents: list[Term],
    ) -> None: ...

    def get_by_terms_values(self, values: set[str]) -> list[Term]: ...
    
    def delete_all(self) -> None: ...

    @property
    def count(self) -> int: ...


class QuestionRepositoryInterface(Protocol):
    def get(self, question: str) -> Question | None:
        ...

    def create(self, question: Question) -> None:
        ...

    def get_question_documents(self, question: str) -> list[Document]:
        ...

    def delete(self, question: str) -> None:
        ...

    def create_many_question_document(self, question_documents: list[QuestionDocument]) -> None:
        ...

    def delete_all(self) -> None:
        ...

    def get_question_answer(self, question: str) -> QuestionAnswer | None:
        ...

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        ...
