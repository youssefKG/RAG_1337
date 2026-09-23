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
from src.core.llm import embeding_model

MAX_CHUNK_SIZE = 2000
CORPUS_PATH = "data/raw/vllm-0.10.1"
RECALL = 10
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"

DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"


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
            embeding_model=embeding_model,
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
    # indexer: Indexer = Indexer(
    #     CORPUS_PATH,
    #     MAX_CHUNK_SIZE,
    #     file_repository=file_repository,
    #     document_term_repository=document_term_repository,
    #     document_repository=document_repository,
    #     embeding_model=embeding_model,
    # )
    # indexer.index()

    set_student_search_result()


if __name__ == "__main__":
    main()


# i dont mean any disrespect but if you say 3hour that mean in this 3hour your understand the subject  and you  learn about the graph  and learn about the algo and you understand it and you implement the algo
