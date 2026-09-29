import os
import sys
import re
from collections.abc import Generator
from collections import Counter
from typing import Annotated, TypeAlias, cast

from tqdm import tqdm

from src.core.config_manager import ConfigManager, IndexingStrategy
from src.core.utils import STOP_WORDS, TOKENIZER_REGEX_PATTERN
from src.core.chunker.languages import Language
from src.core.chunker.text_spliter import TextSpliter
from src.core.entities import Document, File, Term
from src.server.repositories import (
    FileRepositoryInterface,
    DocumentRepositoryInterface,
    TermRepositoryInterface,
)

from src.core.vector_repositories_interfaces import VectorDocumentRepositoryInterface
from src.core.utils import Logger, permission_checker, Stage

ChunkType: TypeAlias = tuple[
    Annotated[str, "chunk"],
    Annotated[int, "start index"],
    Annotated[int, "end index"],
]

_FileType: TypeAlias = tuple[
    Annotated[str, "file_path"],
    Annotated[str, "file_content"],
    Annotated[float, "last updated time"]
]

BATCH_SIZE = 10000

class FileIter:
    def __init__(
            self,
            *,
            files_extensions: tuple[str, ...],
            corpus_path: str,
        ) -> None:
        self.__files: list[_FileType] = list()
        self.__file_extensions: tuple[str, ...] = files_extensions
        self.__corpus_path: str = corpus_path
        self.__length: int = self.__count()

    def __iter__(self) -> Generator[_FileType]:
        for file_path, file_content, last_updated_time in self.__files:
            yield file_path, file_content, last_updated_time

    def __len__(self) -> int:
        return self.__length

    def __count(self) -> int:
        total: int = 0
        for dir_path, _, file_names in os.walk(self.__corpus_path):
            for file_name in file_names:
                if not file_name.endswith(self.__file_extensions):
                    continue
                file_path: str = os.path.join(dir_path, file_name)
                last_updated_time: float = os.path.getmtime(file_path)
                permission_checker(
                    file_path=file_path,
                    read=True,
                    kill=False,
                    fn=lambda x: Logger.warn(x, Stage.INDEXING.name)
                )
                try:
                    with open(file_path, "r") as file:
                        file_content: str = file.read()
                        self.__files.append(
                            (
                                file_path,
                                file_content,
                                last_updated_time
                            )
                        )
                except Exception as error:
                    Logger.warn(str(error), Stage.INDEXING.name)
                    sys.exit(1)
                total += 1
        return total

class Indexer:
    def __init__(
        self,
        /,
        *,
        file_repository: FileRepositoryInterface,
        document_repository: DocumentRepositoryInterface,
        term_repository: TermRepositoryInterface,
        vector_document_repository: VectorDocumentRepositoryInterface,
        config_manager: ConfigManager
    ) -> None:
        self.__file_repository: FileRepositoryInterface = file_repository
        self.__document_repository: DocumentRepositoryInterface = (
            document_repository
        )
        self.__term_repository: TermRepositoryInterface = term_repository
        self.__documents_to_create: list[Document] = list()
        self.__terms_to_create: list[Term] = list()
        self.__files_to_create: list[File] = list()
        self.__vector_document_repository: VectorDocumentRepositoryInterface = (
            vector_document_repository
        )
        self.__config_manager: ConfigManager = config_manager

    def __call__(self, /, *, corpus_path: str, max_chunk_size: int, indexing_strategy: IndexingStrategy) -> None:
        match indexing_strategy:
            case IndexingStrategy.LEXICAL:
                self.__file_repository.delete_all()
                self.__lexical_indexing(max_chunk_size=max_chunk_size, corpus_path=corpus_path)
            case IndexingStrategy.HYBRID:
                pass
            case IndexingStrategy.NONE:
                pass
            case IndexingStrategy.SEMANTIC:
                pass
        try:
            Logger.info(
                "The files is being processed "
                + "stored in the database in smaller chunks for efficient "
                + "retrieval and search. Please wait while the process completes.",
                Stage.INDEXING.name
            )
            self.__file_repository.create_many(self.__files_to_create)
            Logger.info(
                "The document is being processed, and its content is being "
                + "stored in the database in smaller chunks for efficient "
                + "retrieval and search. Please wait while the process completes.",
                Stage.INDEXING.name
            )
            self.__document_repository.create_many(self.__documents_to_create)
            Logger.info(
                "We’re extracting the key terms from your document and storing" 
                + " them in the database to make searching and retrieving" 
                + " relevant information faster.",
                Stage.INDEXING.name
            )
            self.__term_repository.create_many(self.__terms_to_create)
            Logger.info("Embed the documents and store them in vector db", Stage.INDEXING.name)
        except KeyboardInterrupt:
            self.__file_repository.delete_all()
            # TODO: delete all embeded documents
            sys.exit(1)

    def __get_file_status(
            self,
            *,
            file_path: str,
            last_modified_at: float,
        ) -> tuple[File, Annotated[bool, "is file changed"]]:
        file: File | None = self.__file_repository.get_by_path(file_path)
        if file is None:
            file_to_create: File = File(path=file_path, last_modified_at=last_modified_at)
            return file_to_create, True
        elif file.last_modified_at != last_modified_at:
            self.__file_repository.update(id=file.id, last_modified_at=last_modified_at)
            return file, True
        return file, False

    def __lexical_indexing(self, /, *, max_chunk_size: int, corpus_path: str) -> None:
        file_iter: FileIter = FileIter(corpus_path=corpus_path, files_extensions=(".py", ".md", "txt"))
        Logger.info(f"Indexing the corpus: {corpus_path}", Stage.INDEXING.name)
        for file_path, file_content, last_modified_at in tqdm(file_iter, total=len(file_iter)):
            file, is_changed = self.__get_file_status(file_path=file_path, last_modified_at=last_modified_at)
            if is_changed:
                self.__document_repository.delete_by_file_id(file.id)
                self.__vector_document_repository.delete_by_file_id(file.id)
                self.__files_to_create.append(file)
                file_language: Language = self.__get_file_language(file_path)
                self.__index_file_lexical(
                    file=file,
                    file_content=file_content,
                    language=file_language,
                    max_chunk_size=max_chunk_size
                )

    def __index_file_lexical(
        self,
        *,
        file: File,
        file_content: str,
        language: Language,
        max_chunk_size: int,
    ) -> None:
        chunker: TextSpliter = TextSpliter(
            source=file_content,
            overlap_size=0,
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
                length=sum(terms.values())
            )
            self.__documents_to_create.append(document)
            for value, frequency in terms.items():
                term: Term = Term(frequency=frequency, value=value.lower(), document=document)
                self.__terms_to_create.append(term)

    def __get_file_language(self, file_path: str) -> Language:
        if file_path.endswith(".py"):
            return Language.PYTHON
        elif file_path.endswith(".md"):
            return Language.MARKDOWN
        return Language.TEXT

    def embed_documents(self) ->  None:
        pass

    def __get_terms_freqeuncy(self, document: str) -> Counter[str]:
        document_terms: list[str] = [
            word.strip()
            for word in cast(
                list[str],
                re.findall(TOKENIZER_REGEX_PATTERN, document.lower()),
            ) if word.strip() not in STOP_WORDS
        ]
        term_frequency: Counter[str] = Counter(document_terms)
        return term_frequency
