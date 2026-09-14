from typing import cast, Annotated
import os
import fire

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

import django

django.setup()


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
        bm25: BM25Index = BM25Index(
            document_term_repository=document_term_repository,
            document_repository=document_repository,
            top_k=k,
            query=query,
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


def main() -> None:

    _ = fire.Fire(CLI)
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
