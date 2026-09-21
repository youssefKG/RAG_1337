from typing import Annotated, cast
import os
import re

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

import django

django.setup()

from src.data.quetions import QUESTIONS
from src.core.search_algorithms import invert_index, bm25
from src.core.validation_models import (
    RagDataset,
    MinimalSearchResults,
    StudentSearchResults,
    MinimalSource,
)

from src.core.indexer.indexer import Indexer
from src.server.repositories import (
    document_term_repository,
    document_repository,
    file_repository,
)
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS

MAX_CHUNK_SIZE = 2000
CORPUS_PATH = "vllm-0.10.1"
RECALL = 10
CODE_BASE_QUESTIONS = (
    "datasets_public/public/UnansweredQuestions/dataset_code_public.json"
)

DOC_BASE_QUESTIONS = (
    "datasets_public/public/UnansweredQuestions/dataset_docs_public.json"
)


# def get_term_by_id() -> None:
#     terms = document_term_repository.get_by_documet_id(1)
#     for term in terms:
#         print(term.value, term.document.id, term.document.file.path)


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
        pass

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
    for question in QUESTIONS:
        query_terms: list[str] = [
            word
            for word in cast(
                list[str],
                re.findall(r"\b[a-zA-Z0-9]+\b", question.lower()),
            )
            if word not in STOP_WORDS
        ]
        invert_index(query_terms)
        chosen_documents = bm25(query_terms, RECALL)
        print("*" * 30)
        print(question)
        for doc in chosen_documents:
            print(doc.score, doc.document.file.path)

    print(len(QUESTIONS))


def load_unanswerd_question() -> RagDataset:
    unanswered_questions: RagDataset
    with open(CODE_BASE_QUESTIONS, "r") as unanswed_question_file:
        unanswered_questions = RagDataset.model_validate_json(
            unanswed_question_file.read()
        )
    return unanswered_questions


def set_student_search_result() -> None:
    unanswered_questions: RagDataset = load_unanswerd_question()
    minimal_search_results: list[MinimalSearchResults] = list()
    for question in unanswered_questions.rag_questions:
        query_terms: list[str] = [
            word.lower()
            for word in cast(
                list[str],
                re.findall(TOKENIZER_REGEX_PATTERN, question.question.lower()),
            )
            if word not in STOP_WORDS
        ]
        invert_index(query_terms)
        chosen_documents = bm25(query_terms, RECALL)
        minimal_source: list[MinimalSource] = [
            MinimalSource(
                file_path="data/raw/" + chos_doc.document.file.path,
                first_character_index=chos_doc.document.start_index,
                last_character_index=chos_doc.document.end_index,
            )
            for chos_doc in chosen_documents
        ]
        minimal_search_results.append(
            MinimalSearchResults(
                question_id=question.question_id,
                question=question.question,
                retrieved_sources=minimal_source,
            )
        )
        print(question.question)
    student_search_results = StudentSearchResults(
        k=5, search_results=minimal_search_results
    )

    with open("answers.json", "w") as file:
        _ = file.write(student_search_results.model_dump_json(indent=4))


def main() -> None:
    """

    indexer: Indexer = Indexer(
        CORPUS_PATH,
        MAX_CHUNK_SIZE,
        file_repository=file_repository,
        document_term_repository=document_term_repository,
        document_repository=document_repository,
    )
    indexer.index()
    """

    # test_invert_index_with_bm25()
    set_student_search_result()


if __name__ == "__main__":
    main()


# i dont mean any disrespect but if you say 3hour that mean in this 3hour your understand the subject  and you  learn about the graph  and learn about the algo and you understand it and you implement the algo
