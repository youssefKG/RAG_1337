from collections.abc import Generator
from typing import Annotated, TypeAlias

from src.core.chunker.languages import Language
from src.core.chunker.text_spliter import TextSpliter
from src.server.entities import DocumentInterface, FileInterface
from src.server.repositories import (
    FileRepositoryInterface,
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)

from collections import Counter
import os

ChunkType: TypeAlias = tuple[
    Annotated[str, "chunk"],
    Annotated[int, "start index"],
    Annotated[int, "end index"],
]


class Indexer:
    def __init__(
        self,
        corpus_path: str,
        max_chunk_size: int = 1000,
        /,
        *,
        file_repository: FileRepositoryInterface,
        document_repository: DocumentRepositoryInterface,
        document_term_repository: DocumentTermRepositoryInterface,
    ) -> None:
        self.__corpus_path: str = corpus_path
        self.__max_chunk_size: int = max_chunk_size
        self.__file_repository: FileRepositoryInterface = file_repository
        self.__document_repository: DocumentRepositoryInterface = document_repository
        self.__document_term_repository: DocumentTermRepositoryInterface = (
            document_term_repository
        )
        self.__documents_to_create: list[
            tuple[
                Annotated[int, "start index"],
                Annotated[int, "end_index"],
                Annotated[int, "file id"],
                Annotated[int, "document length"],
            ]
        ] = list()
        self.__terms_to_create: list[
            tuple[
                Annotated[int, "term frequency"],
                Annotated[str, "term value"],
                Annotated[int, "document id"],
            ]
        ] = list()
        self.unique_terms: set[tuple[str, int]] = set()
        self.__total_terms: set[str] = set()

    def index(self) -> None:
        for file_path, file_content, last_modified_at in self.__files_iter():
            file, is_changed = self.__insert_file(
                file_path=file_path, last_modified_at=last_modified_at
            )
            if is_changed:
                print("Changed: ", file_path)
                language: Language = self.__get_language(file_path)
                self.__index_file(
                    file=file, file_content=file_content, language=language
                )
            else:
                print("Not changed: ", file_path)
        created_documents: list[DocumentInterface] = (
            self.__document_repository.create_many(self.__documents_to_create)
        )
        terms_to_create = [
            (frequency, value, created_documents[document_id - 1].id)
            for frequency, value, document_id in self.__terms_to_create
        ]
        self.__document_term_repository.create_many(terms_to_create)
        print(len(self.__total_terms))

    def __files_iter(
        self,
    ) -> Generator[
        tuple[
            Annotated[str, "file path"],
            Annotated[str, "file content"],
            Annotated[float, "last updated time"],
        ]
    ]:
        for dirpath, _, filenames in os.walk(self.__corpus_path):
            for file_name in filenames:
                file_path: str = os.path.join(dirpath, file_name)
                if not file_path.endswith((".py", ".md")):
                    continue
                try:
                    last_modified_time: float = os.path.getmtime(file_path)
                    with open(file_path, "r") as file:
                        yield file_path, file.read(), last_modified_time
                except Exception as error:
                    print(error)

    def __insert_file(
        self, *, file_path: str, last_modified_at: float
    ) -> tuple[FileInterface, Annotated[bool, "is file changed"]]:
        # check if the file is already exist
        is_changed: bool = False
        file, is_created = self.__file_repository.get_or_create_by_path(
            path=file_path, last_modified_at=last_modified_at
        )
        if is_created:
            is_changed = True
            return file, is_changed
        if file.last_modified_at != last_modified_at:
            is_changed = True
            self.__file_repository.update(id=file.id, last_modified_at=last_modified_at)
        return file, is_changed

    def __index_file(
        self, *, file: FileInterface, file_content: str, language: Language
    ) -> None:
        # delete documents for this file
        self.__document_repository.delete_by_file_id(file.id)
        # delete terms for this file
        chunker: TextSpliter = TextSpliter(
            source=file_content,
            overlap_size=0,
            max_chunk_size=self.__max_chunk_size,
            language=language,
        )
        chunks: list[ChunkType] = chunker.split_text()

        for chunk, start_index, end_index in chunks:
            terms: Counter[str] = self.__get_terms_freqeuncy(chunk + file.path)
            self.__total_terms.update(set(terms.keys()))
            self.__documents_to_create.append(
                (start_index, end_index, len(chunk), file.id)
            )
            for (
                term,
                frequency,
            ) in terms.items():
                if (term, len(self.__documents_to_create)) not in self.unique_terms:
                    self.__terms_to_create.append(
                        (frequency, term, len(self.__documents_to_create))
                    )
                    self.unique_terms.add((term, len(self.__documents_to_create)))

    def __get_language(self, file_path: str) -> Language:
        if file_path.endswith(".py"):
            return Language.PYTHON
        elif file_path.endswith(".md"):
            return Language.MARKDOWN
        return Language.TEXT

    def __get_terms_freqeuncy(self, document: str) -> Counter[str]:
        tokens: list[str] = document.split()
        term_frequency: Counter[str] = Counter(tokens)
        return term_frequency
