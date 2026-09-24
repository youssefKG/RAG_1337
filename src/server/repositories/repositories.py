from typing import Annotated, Protocol
from src.server.entities import (
    DocumentTermInterface,
    DocumentInterface,
    FileInterface,
)


class FileRepositoryInterface(Protocol):
    def create(self, *, path: str, last_modified_at: float) -> FileInterface: ...

    def delete_by_path(self, path: str) -> None: ...

    def delete_by_id(self, file_id: int) -> None: ...

    def get_by_path(self, path: str) -> FileInterface | None: ...

    def get_or_create_by_path(
        self,
        *,
        path: str,
        last_modified_at: float,
    ) -> tuple[FileInterface, Annotated[bool, "is created"]]: ...

    def update(
        self,
        /,
        *,
        id: int,
        path: str | None = None,
        last_modified_at: float | None = None,
    ) -> None: ...


class DocumentRepositoryInterface(Protocol):

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
    ) -> list[DocumentInterface]: ...

    @property
    def get_avg_document_length(self) -> float: ...

    def delete_by_file_id(self, file_id: int) -> None: ...

    @property
    def count(self) -> int: ...

    def get_by_terms_values(self, values: set[str]) -> list[DocumentInterface]: ...

    def all(self) -> list[DocumentInterface]:
        ...


class DocumentTermRepositoryInterface(Protocol):
    def create(
        self, *, term_frequency: int, term_value: str, document_id: int
    ) -> DocumentTermInterface: ...

    def create_many(
        self,
        terms_documents: list[
            tuple[
                Annotated[int, "term frequency"],
                Annotated[str, "term value"],
                Annotated[int, "document id"],
            ]
        ],
    ) -> None: ...

    def get_by_terms_values(self, values: set[str]) -> list[DocumentTermInterface]: ...
