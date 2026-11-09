"""
Corpus indexing module for the Rage Against Machine RAG system.

This module implements the lexical and semantic indexing pipelines.

Responsibilities:
    - Discover supported files in the source corpus.
    - Detect new and modified files.
    - Split files into documents using language-aware chunking.
    - Extract terms and calculate their frequencies.
    - Persist files, documents, and terms in the database.
    - Generate semantic vector representations for documents.
    - Manage indexing strategies and batch processing.

The indexing process supports lexical, semantic, hybrid, and
incremental indexing strategies.

Batch configuration:
    LEXICAL_BATCH_SIZE: Maximum lexical document batch threshold.
    SEMANTIC_BATCH_SIZE: Semantic document batch size.
"""

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


_FileType: TypeAlias = tuple[
    Annotated[str, "file_path"],
    Annotated[str, "file_content"],
    Annotated[float, "last updated time"],
]

ChunkType: TypeAlias = tuple[
    Annotated[str, "chunk"],
    Annotated[int, "start index"],
    Annotated[int, "end index"],
]


LEXICAL_BATCH_SIZE = 8000
SEMANTIC_BATCH_SIZE = 800


class IndexerError(Exception):
    """Raised when an indexing operation encounters an error."""


class FileIter:
    """
    Lazy iterator over supported files in a corpus.

    Traverses the corpus directory recursively and yields readable
    files matching the configured extensions.

    The iterator also maintains the total number of files for
    progress reporting.

    Attributes:
        __file_extensions: Supported file extensions.
        __corpus_path: Root directory of the corpus.
        __length: Number of files reported by the counter.
    """

    def __init__(
        self,
        *,
        files_extensions: tuple[str, ...],
        corpus_path: str,
    ) -> None:
        """
        Initialize the corpus file iterator.

        Args:
            files_extensions: Supported file extensions.
            corpus_path: Root directory to traverse.
        """
        self.__file_extensions: tuple[str, ...] = files_extensions
        self.__corpus_path: str = corpus_path
        self.__length: int = self.__count()

    def __iter__(self) -> Generator[_FileType]:
        """
        Iterate over readable files matching the supported extensions.

        Yields:
            _FileType: A tuple containing the file path, content,
                and last modification timestamp.

        Raises:
            IndexerError: If reading a file fails.
        """
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
        """
        Return the number of files reported by the internal counter.

        Returns:
            int: Number of files in the corpus according to __count().
        """
        return self.__length

    def __count(self) -> int:
        """
        Count files recursively in the corpus directory.

        Returns:
            int: Number of files matching the counting condition.
        """
        return sum(
            1
            for _, _, file_names in os.walk(self.__corpus_path)
            for file in file_names
            if not file.endswith(self.__file_extensions)
        )


class Indexer:
    """
    Coordinate lexical and semantic indexing operations.

    The Indexer acts as the main indexing service of the RAG system.

    It coordinates repositories, configuration management, corpus
    traversal, document chunking, term extraction, and vector indexing.

    Supported indexing strategies:
        LEXICAL: Build the lexical index.
        HYBRID: Build both lexical and semantic indexes.
        SEMANTIC: Build the semantic index from existing documents.
        NONE: Apply incremental indexing when new or modified files exist.

    Repository dependencies are injected through the constructor.
    """

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
        """
        Initialize the indexer with its required dependencies.

        Args:
            file_repository: Repository managing indexed files.
            document_repository: Repository managing lexical documents.
            term_repository: Repository managing document terms.
            vector_document_repository: Repository managing semantic
                document representations.
            config_manager: Manages indexing configuration and strategies.
            question_repository: Repository managing indexed questions.
        """
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
        """
        Execute the indexing pipeline using the configured strategy.

        Determines the appropriate indexing strategy, prepares existing
        indexes when necessary, and executes lexical or semantic indexing.

        Database operations are executed within an atomic transaction.

        Args:
            corpus_path: Root directory of the source corpus.
            max_chunk_size: Maximum allowed document chunk size.
            is_hybrid: Whether hybrid retrieval is enabled.

        Returns:
            None.

        Raises:
            IndexerError: If a database operation raises CustomDatabaseError.
        """
        files: list[_FileType]
        documents: list[Document]

        indexing_strategy: IndexingStrategy = (
            self.__config_manager.get_indexing_strategy(
                max_chunk_size, is_hybrid
            )
        )

        files_to_index_callback: Callable[
            [],
            tuple[list[_FileType], Annotated[set[str], "files_path"]]
        ] = lambda: self.__get_files_to_index(corpus_path)

        lexical_indexing_callback: Callable[
            [list[_FileType]], list[Document]
        ] = lambda files: self.__lexical_indexing(
            files=files, max_chunk_size=max_chunk_size, corpus_path=corpus_path
        )

        Logger.info(f"INDEXING STRATEGY: {indexing_strategy.name}", __name__)
        files_paths: set[str] = set()

        try:
            with transaction_atomic():
                self.__prepare_new_indexing_strategy(indexing_strategy)
                match indexing_strategy:
                    case IndexingStrategy.LEXICAL:
                        files, files_paths = files_to_index_callback()
                        _ = lexical_indexing_callback(files)
                    case IndexingStrategy.HYBRID:
                        files, files_paths = files_to_index_callback()
                        documents = lexical_indexing_callback(files)
                        self.__semantic_indexing(documents)

                    case IndexingStrategy.SEMANTIC:
                        documents = self.__document_repository.all()
                        self.__semantic_indexing(documents)

                    case IndexingStrategy.NONE:
                        files, files_paths = files_to_index_callback()
                        if len(files) > 0:
                            documents = lexical_indexing_callback(files)
                            if is_hybrid:
                                self.__semantic_indexing(documents)
                if not files_paths:
                    self.__file_repository.delete_by_files_paths(files_paths)
            self.__config_manager.update_indexing_config(
                max_chunk_size=max_chunk_size, is_hybrid=is_hybrid
            )

        except CustomDatabaseError as error:
            raise IndexerError(
                f"Database Error {str(error)}"
            ) from error

    def __prepare_new_indexing_strategy(
        self,
        new_indexing_strategy: IndexingStrategy
    ) -> None:
        """
        Prepare existing indexes before executing a new indexing strategy.

        Depending on the requested strategy, removes existing file records,
        semantic representations, and questions to prevent stale indexing
        data from being retained.

        Args:
            new_indexing_strategy: Strategy selected for the next indexing
                operation.

        Returns:
            None.
        """
        preindexing_strategy: IndexingStrategy = (
            self.__config_manager.indexing_strategy
        )

        if new_indexing_strategy in (
            IndexingStrategy.LEXICAL,
            IndexingStrategy.HYBRID,
            IndexingStrategy.SEMANTIC
        ):
            if new_indexing_strategy != IndexingStrategy.SEMANTIC:
                if preindexing_strategy == IndexingStrategy.LEXICAL:
                    Logger.info(
                        "Deleting the old lexical indexing documents"
                        + " and vector documents",
                        "INDEXING",
                    )

                self.__file_repository.delete_all()

            Logger.info(
                "Delete the old semantic indexing if exist",
                "INDEXING"
            )
            self.__vector_document_repository.delete_all()

            Logger.info(
                "Delete all questions and their answers, "
                + "and their relevant documents",
                "INDEXING"
            )
            self.__question_repository.delete_all()

    def __get_files_to_index(
        self,
        corpust_path: str
    ) -> tuple[list[_FileType], Annotated[set[str], "files paths"]]:
        """
        Discover new and modified files that require indexing.

        Compares the modification timestamps of corpus files against
        their previously indexed records.

        New files are scheduled for indexing. Modified files have their
        existing file and vector records deleted before being scheduled.

        Args:
            corpust_path: Root directory of the source corpus.

        Returns:
            list[_FileType]: Files requiring indexing, including their
                paths, contents, and modification timestamps.
        """
        file_iter: FileIter = FileIter(
            corpus_path=corpust_path,
            files_extensions=(".py", ".txt", ".md")
        )
        files_paths: set[str] = set()

        files_to_index: list[_FileType] = list()
        for file_path, file_content, last_modified_at in file_iter:
            file: File | None = self.__file_repository.get_by_path(file_path)
            if file_path not in files_paths:
                files_paths.add(file_path)
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
        return files_to_index, files_paths

    def __lexical_indexing(
        self,
        /,
        *,
        files: list[_FileType],
        max_chunk_size: int,
        corpus_path: str,
    ) -> list[Document]:
        """
        Perform lexical indexing for the supplied corpus files.

        Each file is split into language-aware chunks. Terms are extracted
        from every chunk and their frequencies are calculated.

        Files, documents, and terms are persisted in batches.

        Args:
            files: Files scheduled for indexing.
            max_chunk_size: Maximum allowed chunk size.
            corpus_path: Root directory of the source corpus.

        Returns:
            list[Document]: All documents generated during lexical indexing.
        """
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
                path=file_path,
                last_modified_at=last_modified_at
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
        """
        Generate and persist semantic representations of documents.

        Processes documents in batches using the configured semantic
        batch size and delegates vector creation to the vector repository.

        Args:
            documents: Documents whose semantic representations
                must be indexed.

        Returns:
            None.
        """
        total_documents: list[Document] = documents
        batch_documents: list[Document]
        for idx in tqdm(
            range(
                    0,
                    len(total_documents),
                    SEMANTIC_BATCH_SIZE
                ),
            desc="Semantic Indexing: "
        ):
            batch_documents = total_documents[idx:idx + SEMANTIC_BATCH_SIZE]
            self.__vector_document_repository.create_many(batch_documents)

    def __index_file_lexical(
        self,
        *,
        file: File,
        file_content: str,
        language: Language,
        max_chunk_size: int,
    ) -> tuple[list[Document], list[Term]]:
        """
        Split a file into documents and extract their lexical terms.

        Uses TextSpliter to generate chunks with their original character
        positions. Each chunk becomes a Document entity, and its extracted
        terms are represented by Term entities with their frequencies.

        Args:
            file: File entity associated with the source content.
            file_content: Original file content.
            language: Programming or document language used for processing.
            max_chunk_size: Maximum allowed chunk size.

        Returns:
            tuple[list[Document], list[Term]]: Generated documents and
                their corresponding term entities.
        """
        terms_to_create: list[Term] = list()
        documents_to_create: list[Document] = list()

        chunker: TextSpliter = TextSpliter(
            source=file_content,
            max_chunk_size=max_chunk_size,
            language=language,
        )

        chunks: list[ChunkType] = chunker.split_text()

        terms: Counter[str]

        for chunk, start_index, end_index in chunks:
            if language == Language.PYTHON:
                terms = self.__get_terms_freqeuncy_python(chunk)
            else:
                terms = self.__get_terms_freqeuncy_markdown_text(chunk)

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
                    frequency=frequency,
                    value=value.lower(),
                    document=document
                )

                terms_to_create.append(term)

        return documents_to_create, terms_to_create

    def __get_file_language(self, file_path: str) -> Language:
        """
        Determine the processing language from a file extension.

        Args:
            file_path: Path of the source file.

        Returns:
            Language: PYTHON for Python files, MARKDOWN for Markdown files,
                and TEXT for other supported files.
        """
        if file_path.endswith(".py"):
            return Language.PYTHON
        elif file_path.endswith(".md"):
            return Language.MARKDOWN
        return Language.TEXT

    def __get_terms_freqeuncy_markdown_text(
        self, document: str
    ) -> Counter[str]:
        """
        Extract normalized term frequencies from document text.

        Tokenizes the text using the configured tokenizer pattern,
        removes stop words, and calculates the frequency of each term.

        Args:
            document: Text content to tokenize.

        Returns:
            Counter[str]: Mapping of terms to their occurrence frequencies.
        """
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

    def __get_terms_freqeuncy_python(self, text: str) -> Counter[str]:
        """
        Extract term frequencies from Python source code.

        Tokenizes Python source text, removes stop words, and expands
        compound identifiers by separating camelCase and snake_case
        components into additional searchable terms.

        Args:
            text: Python source code to tokenize.

        Returns:
            Counter[str]: Mapping of normalized terms to their
                occurrence frequencies.
        """
        splited_text: list[str] = re.findall(TOKENIZER_REGEX_PATTERN, text)
        tokens: list[str] = []
        for token in splited_text:
            if token in STOP_WORDS:
                continue
            tokens.append(token.lower())

            expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", token)
            parts = expanded.replace("_", " ").lower().split()
            if len(parts) > 1:
                tokens.extend(parts)
        return Counter(tokens)
