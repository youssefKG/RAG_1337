import os
import re
from collections.abc import Generator, Callable
from collections import Counter
from typing import Annotated, TypeAlias, cast

from tqdm import tqdm

from src.core.config_manager import IndexingStrategy, ConfigManager
from src.core.utils import STOP_WORDS, TOKENIZER_REGEX_PATTERN
from src.core.chunker.languages import Language
from src.core.chunker.text_spliter import TextSpliter
from src.core.entities import Document, File, Term
from src.server.repositories import (
    FileRepositoryInterface,
    DocumentRepositoryInterface,
    TermRepositoryInterface,
    QuestionRepositoryInterface,
    transaction_atomic,
)
from src.core.vector_repositories_interfaces import (
    VectorDocumentRepositoryInterface,
)
from src.core.utils import Logger, permission_checker, Stage
from src.server.errors import CustomDatabaseError

ChunkType: TypeAlias = tuple[
    Annotated[str, "chunk"],
    Annotated[int, "start index"],
    Annotated[int, "end index"],
]

_FileType: TypeAlias = tuple[
    Annotated[str, "file_path"],
    Annotated[str, "file_content"],
    Annotated[float, "last updated time"],
]

BATCH_SIZE = 10000
LEXICAL_BATCH_SIZE = 5000
SEMANTIC_BATCH_SIZE = 1000


class IndexerError(Exception):
    ...


class FileIter:
    def __init__(
        self,
        *,
        files_extensions: tuple[str, ...],
        corpus_path: str,
    ) -> None:
        self.__file_extensions: tuple[str, ...] = files_extensions
        self.__corpus_path: str = corpus_path
        self.__length: int = self.__count()

    def __iter__(self) -> Generator[_FileType]:
        for dir_path, _, file_names in os.walk(self.__corpus_path):
            for file_name in file_names:
                file_path: str = os.path.join(dir_path, file_name)
                if not file_name.endswith(self.__file_extensions):
                    continue
                if permission_checker(
                    file_path=file_path,
                    read=True,
                    kill=False,
                    fn=lambda x: Logger.warn(x, Stage.INDEXING.name),
                ):
                    last_updated_time = os.path.getmtime(file_path)
                    try:
                        with open(file_path, "r") as file:
                            file_content: str = file.read()
                            yield file_path, file_content, last_updated_time
                    except Exception as error:
                        raise IndexerError(str(error)) from error

    def __len__(self) -> int:
        return self.__length

    def __count(self) -> int:
        return sum(
            1
            for _, _, file_names in os.walk(self.__corpus_path)
            for file in file_names
            if not file.endswith(self.__file_extensions)
        )


class Indexer:
    def __init__(
        self,
        /,
        *,
        file_repository: FileRepositoryInterface,
        document_repository: DocumentRepositoryInterface,
        term_repository: TermRepositoryInterface,
        vector_document_repository: VectorDocumentRepositoryInterface,
        config_manager: ConfigManager,
        question_repository: QuestionRepositoryInterface,
    ) -> None:
        self.__file_repository: FileRepositoryInterface = file_repository
        self.__document_repository: DocumentRepositoryInterface = (
            document_repository
        )
        self.__term_repository: TermRepositoryInterface = term_repository
        self.__vector_document_repository: (
            VectorDocumentRepositoryInterface
        ) = vector_document_repository
        self.__question_repository: QuestionRepositoryInterface = (
            question_repository
        )
        self.__config_manager: ConfigManager = config_manager

    def __call__(
        self, /, *, corpus_path: str, max_chunk_size: int, is_hybrid: bool
    ) -> None:
        files: list[_FileType]
        documents: list[Document]
        indexing_strategy: IndexingStrategy = (
            self.__config_manager.get_indexing_strategy(
                max_chunk_size, is_hybrid
            )
        )
        files_to_index_callback: Callable[[], list[_FileType]] = (
            lambda: self.__get_files_to_index(corpus_path)
        )
        lexical_indexing_callback: Callable[
            [list[_FileType]], list[Document]
        ] = lambda files: self.__lexical_indexing(
            files=files, max_chunk_size=max_chunk_size, corpus_path=corpus_path
        )
        Logger.info(f"INDEXING STRATEGY: {indexing_strategy.name}", __name__)
        try:
            with transaction_atomic():
                match indexing_strategy:
                    case IndexingStrategy.LEXICAL:
                        Logger.info(
                            "Deleting the old indexing documents"
                            + " and vector documents",
                            "INDEXING",
                        )
                        self.__file_repository.delete_all()
                        self.__question_repository.delete_all()
                        self.__vector_document_repository.delete_all()
                        files = files_to_index_callback()
                        _ = lexical_indexing_callback(files)
                    case IndexingStrategy.HYBRID:
                        Logger.info(
                            "Deleting the old indexing documents"
                            + " and vector documents",
                            "INDEXING",
                        )
                        self.__file_repository.delete_all()
                        self.__question_repository.delete_all()
                        self.__vector_document_repository.delete_all()
                        files = files_to_index_callback()
                        documents = lexical_indexing_callback(files)
                        self.__semantic_indexing(documents)
                    case IndexingStrategy.SEMANTIC:
                        self.__vector_document_repository.delete_all()
                        self.__question_repository.delete_all()
                        documents = self.__document_repository.all()
                        self.__semantic_indexing(documents)
                    case IndexingStrategy.NONE:
                        files = files_to_index_callback()
                        if len(files) > 0:
                            documents = lexical_indexing_callback(files)
                            if is_hybrid:
                                self.__semantic_indexing(documents)
            self.__config_manager.update_indexing_config(
                max_chunk_size=max_chunk_size, is_hybrid=is_hybrid
            )
        except CustomDatabaseError as error:
            raise IndexerError(str(error)) from error

    def __get_files_to_index(self, corpust_path: str) -> list[_FileType]:
        file_iter: FileIter = FileIter(
            corpus_path=corpust_path, files_extensions=(".py", ".txt", ".md")
        )
        files_to_index: list[_FileType] = list()
        for file_path, file_content, last_modified_at in tqdm(file_iter, total=len(file_iter), desc="Search for changed file"):
            file: File | None = self.__file_repository.get_by_path(file_path)
            if file is None:
                files_to_index.append(
                    (file_path, file_content, last_modified_at)
                )
            elif file.last_modified_at != last_modified_at:
                self.__file_repository.delete_by_id(file.id)
                self.__vector_document_repository.delete_by_file_id(file.id)
                files_to_index.append(
                    (file_path, file_content, last_modified_at)
                )
                Logger.warn(
                    f"the file is been changed {file_path}", "INDEXING"
                )
        return files_to_index

    def __lexical_indexing(
        self,
        /,
        *,
        files: list[_FileType],
        max_chunk_size: int,
        corpus_path: str,
    ) -> list[Document]:
        Logger.info(f"Indexing the corpus: {corpus_path}", Stage.INDEXING.name)
        documents_to_create: list[Document] = list()
        files_to_create: list[File] = list()
        terms_to_create: list[Term] = list()
        total_documents: list[Document] = list()
        for idx, (file_path, file_content, last_modified_at) in enumerate(
            tqdm(files, total=len(files), desc="lexical indexing: ")
        ):
            file_language: Language = self.__get_file_language(file_path)
            file: File = File(
                path=file_path, last_modified_at=last_modified_at
            )
            files_to_create.append(file)
            documents, terms = self.__index_file_lexical(
                file=file,
                file_content=file_content,
                language=file_language,
                max_chunk_size=max_chunk_size,
            )
            total_documents.extend(documents)
            documents_to_create.extend(documents)
            terms_to_create.extend(terms)
            if len(documents_to_create) > LEXICAL_BATCH_SIZE:
                self.__file_repository.create_many(files_to_create)
                self.__document_repository.create_many(documents_to_create)
                self.__term_repository.create_many(terms_to_create)
                files_to_create.clear()
                terms_to_create.clear()
                documents_to_create.clear()
            elif idx == len(files) - 1:
                self.__file_repository.create_many(files_to_create)
                self.__document_repository.create_many(documents_to_create)
                self.__term_repository.create_many(terms_to_create)
        return total_documents

    def __semantic_indexing(self, documents: list[Document]) -> None:
        total_documents: list[Document] = documents
        batch_documents: list[Document]
        for idx in tqdm(
            range(0, len(documents), SEMANTIC_BATCH_SIZE),
            desc="SEAMANTIC INDEXING",
        ):
            if idx > SEMANTIC_BATCH_SIZE:
                batch_documents = total_documents[:SEMANTIC_BATCH_SIZE]
                self.__vector_document_repository.create_many(batch_documents)
                total_documents = total_documents[SEMANTIC_BATCH_SIZE:]
            elif idx == len(documents) - 1:
                self.__vector_document_repository.create_many(total_documents)
                total_documents.clear()

    def __index_file_lexical(
        self,
        *,
        file: File,
        file_content: str,
        language: Language,
        max_chunk_size: int,
    ) -> tuple[list[Document], list[Term]]:
        terms_to_create: list[Term] = list()
        documents_to_create: list[Document] = list()
        chunker: TextSpliter = TextSpliter(
            source=file_content,
            max_chunk_size=max_chunk_size,
            language=language,
        )
        chunks: list[ChunkType] = chunker.split_text()
        for chunk, start_index, end_index in chunks:
            terms: Counter[str] = self.__get_terms_freqeuncy(chunk)
            document: Document = Document(
                file=file,
                start_index=start_index,
                end_index=end_index,
                content=chunk,
                length=sum(terms.values()),
            )
            documents_to_create.append(document)
            for value, frequency in terms.items():
                term: Term = Term(
                    frequency=frequency, value=value.lower(), document=document
                )
                terms_to_create.append(term)
        return documents_to_create, terms_to_create

    def __get_file_language(self, file_path: str) -> Language:
        if file_path.endswith(".py"):
            return Language.PYTHON
        elif file_path.endswith(".md"):
            return Language.MARKDOWN
        return Language.TEXT

    def __get_terms_freqeuncy(self, document: str) -> Counter[str]:
        document_terms: list[str] = [
            word.strip()
            for word in cast(
                list[str],
                re.findall(TOKENIZER_REGEX_PATTERN, document.lower()),
            )
            if word.strip() not in STOP_WORDS
        ]
        term_frequency: Counter[str] = Counter(document_terms)
        return term_frequency
