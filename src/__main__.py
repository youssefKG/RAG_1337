from typing import Annotated
import os

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

import django

django.setup()

from src.core.search_engine import search_engine
from src.core.validation_models import (
    RagDataset,
    MinimalSearchResults,
    StudentSearchResults,
)

from src.core.indexer.indexer import Indexer
from src.server.repositories import (
    document_term_repository,
    document_repository,
    file_repository,
)
from src.core.rage_against_machine import RageAgainstMachine
import fire

MAX_CHUNK_SIZE = 2000
CORPUS_PATH = "data/raw/vllm-0.10.1"
RECALL = 10
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"

DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"


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
        print(question.question)
        minimal_search_results.append(search_engine(question, RECALL))
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
    _: object = fire.Fire(RageAgainstMachine)

    # set_student_search_result()


if __name__ == "__main__":
    main()
