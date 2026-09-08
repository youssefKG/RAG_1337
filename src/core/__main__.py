import os

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

import django

django.setup()


from src.core.indexer.indexer import Indexer
from src.server.repositories import (
    document_term_repository,
    document_repository,
    file_repository,
)
from src.server.entities import DocumentTermInterface, FileInterface, DocumentInterface
from src.core.search_algorithms.BM25_index import BM25Index

MAX_CHUNK_SIZE = 1000
CORPUS_PATH = "vllm-0.10.1"


def display_files() -> None:
    files: list[FileInterface] = file_repository.all()
    print("*" * 10, "FILE TABLE", "*" * 10)
    for file in files:
        print(
            f"id: {file.id} | path: {file.path} | last modified at: {file.last_modified_at}"
        )


def display_documents() -> None:
    documents: list[DocumentInterface] = document_repository.all()
    print("*" * 10, "DOCUMENT TABLE", "*" * 10)
    for doc in documents:
        print("document id: ", doc.id)
        print("start index ", doc.start_index)
        print("end index ", doc.end_index)
        print("document length: ", doc.length)
        print("_" * 10)


def display_documents_terms() -> None:
    print("*" * 10, "DOCUMENT TERM TABLE", "*" * 10)
    documents_terms: list[DocumentTermInterface] = document_term_repository.all()
    for doc_term in documents_terms:
        print("document term id: ", doc_term.id)
        print("document term value: ", doc_term.value)
        print(" document term frequency: ", doc_term.frequency)


def display() -> None:
    documents: list[DocumentTermInterface] = document_term_repository.all()
    for document in documents:
        print("document term id: ", document.id)
        print("document term value: ", document.value)
        print("document frequency: ", document.frequency)


def print_document_has_term_value() -> None:
    documents: list[DocumentInterface] = (
        document_repository.get_documents_has_term_value("name")
    )
    for document in documents:
        print("document id: ", document.id)
        # print("document term value: ", document.value)
        # print("document frequency: ", document.frequency)
        print("file path: ", document.file.path)
        print("start_index: ", document.start_index)
        print("end_index: ", document.end_index)


def test_bm25() -> None:
    bm25_search: BM25Index = BM25Index(
        document_term_repository=document_term_repository,
        document_repository=document_repository,
        top_k=20,
        query="""What determines whether custom allreduce is enabled in vLLM's CudaCommunicator?""",
    )
    bm25_search.search()
    condidate_documents = bm25_search.documents_score
    print(condidate_documents)
    documents: list[DocumentInterface] = document_repository.get_by_ids(
        condidate_documents
    )
    print(condidate_documents)
    for document in documents:
        print("document id: ", document.id)
        # print("document term value: ", document.value)
        # print("document frequency: ", document.frequency)
        print("file path: ", document.file.path)
        print("start_index: ", document.start_index)
        print("end_index: ", document.end_index)


def get_term_by_id() -> None:
    terms = document_term_repository.get_by_documet_id(1)
    for term in terms:
        print(term.value, term.document.id, term.document.file.path)


def main() -> None:
    indexer: Indexer = Indexer(
        CORPUS_PATH,
        MAX_CHUNK_SIZE,
        file_repository=file_repository,
        document_repository=document_repository,
        document_term_repository=document_term_repository,
    )
    indexer.index()

    # display_files()
    # display_terms()
    # display_documents()
    # print_document_has_term_value()
    # display_documents_terms()
    test_bm25()
    # get_term_by_id()


if __name__ == "__main__":
    main()


# i dont mean any disrespect but if you say 3hour that mean in this 3hour your understand the subject  and you  learn about the graph  and learn about the algo and you understand it and you implement the algo
