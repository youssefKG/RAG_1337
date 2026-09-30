from typing import Annotated, Protocol
from src.core.entities import (
    Term,
    Document,
    File,
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



class TermRepositoryInterface(Protocol):
    def create_many(
        self,
        terms_documents: list[Term],
    ) -> None: ...

    def get_by_terms_values(self, values: set[str]) -> list[Term]: ...
    
    def delete_all(self) -> None: ...

    @property
    def count(self) -> int: ...

