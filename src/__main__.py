from typing import Annotated
import os
import fire

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

import django

django.setup()
from src.data.quetions import QUESTIONS
from src.core.search_algorithms.invert_index import InvertIndex


from src.core.indexer.indexer import Indexer
from src.server.repositories import (
    document_term_repository,
    document_repository,
    file_repository,
)
from src.core.search_algorithms.BM25_index import BM25Index

MAX_CHUNK_SIZE = 2000
CORPUS_PATH = "vllm-0.10.1"


def get_term_by_id() -> None:
    terms = document_term_repository.get_by_documet_id(1)
    for term in terms:
        print(term.value, term.document.id, term.document.file.path)


class CLI:

    def __init__(self, invert_index: InvertIndex) -> None:
        self.__invert_index: InvertIndex = invert_index

    def index(self, max_chunk_size: int = 2000) -> None:
        if max_chunk_size == True:
            max_chunk_size = 2000
        indexer: Indexer = Indexer(
            CORPUS_PATH,
            max_chunk_size,
            file_repository=file_repository,
            document_term_repository=document_term_repository,
            document_repository=document_repository,
        )
        indexer.index()

    def search(self, query: str, k: int = 5) -> None:
        invert_index: InvertIndex = InvertIndex(
            document_term_repository=document_term_repository,
            document_repository=document_repository,
        )
        for question in QUESTIONS:
            bm25: BM25Index = BM25Index(
                document_term_repository=document_term_repository,
                document_repository=document_repository,
                top_k=k,
                query=query,
                invert_index=invert_index(question),
            )
            bm25.search()

    def search_dataset(
        self,
        data_set_path: str,
        path: str,
        k: int,
        save_directory: str,
        dir: Annotated[str, "save_directory_path"],
    ) -> None:
        pass

    def answer(self, query: str, k: int) -> None:
        pass

    def answer_dataset(
        self, student_search_result_path: str, path: str, save_directory: str, dir: str
    ) -> None:
        pass

    def evaluate(
        self,
    ) -> None:
        pass


def test_invert_index_with_bm25() -> None:
    indexer: Indexer = Indexer(
        CORPUS_PATH,
        MAX_CHUNK_SIZE,
        file_repository=file_repository,
        document_term_repository=document_term_repository,
        document_repository=document_repository,
    )
    indexer.index()
    invert_index: InvertIndex = InvertIndex(
        document_term_repository=document_term_repository,
        document_repository=document_repository,
    )
    k: int = 5

    for question in QUESTIONS:
        bm25: BM25Index = BM25Index(
            document_term_repository=document_term_repository,
            document_repository=document_repository,
            top_k=k,
            query=question,
            invert_index=invert_index(question),
        )
        bm25.search()


def main() -> None:
    test_invert_index_with_bm25()
    """

    invert_index: InvertIndex = InvertIndex(
        document_term_repository=document_term_repository,
        document_repository=document_repository,
    )
    cli: CLI = CLI(invert_index=invert_index)

    _ = fire.Fire(cli)
    """
    # display_files()
    # display_terms()
    # display_documents()
    # print_document_has_term_value()
    # display_documents_terms()
    # test_bm25()
    # get_term_by_id()


if __name__ == "__main__":
    main()


# i dont mean any disrespect but if you say 3hour that mean in this 3hour your understand the subject  and you  learn about the graph  and learn about the algo and you understand it and you implement the algo
