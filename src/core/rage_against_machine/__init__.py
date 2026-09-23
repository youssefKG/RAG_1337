from src.core.search_engine import SearchEngine, search_engine
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    RagDataset,
)
from src.core.utils.logger import Logger
from src.core.indexer import indexer, Indexer
import os

import sys

CORPUS_PATH = "data/raw/vllm-0.10.1"
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"
DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"
DATASET_PATH = "data/datasets/UnansweredQuestions/"
STUDENT_SEARCH_RESULTS_PATH = (
    "data/datasets/UnansweredQuestions/dataset_docs_public.json"
)
SAVE_DIRECTORY = "data/output/search_results/UnansweredQuestions"

DATA_PROCESSED_DIR = "data/processed/"
MAX_CHUNK_SIZE = 2000


class RageAgainstMachine:
    def __init__(self) -> None:
        self.__search_engine: SearchEngine = search_engine
        self.__indexer: Indexer = indexer

    def index(self, max_chunk_size: int = MAX_CHUNK_SIZE) -> None:
        if not os.path.exists(DATA_PROCESSED_DIR):
            os.makedirs(DATA_PROCESSED_DIR)
        self.__indexer(corpus_path=CORPUS_PATH, max_chunk_size=max_chunk_size)

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> None:
        if k == 0:
            Logger.error(
                "Number of requested results 0 cannot be 0 or negative.",
                "SEARCH_DATASET",
            )
            sys.exit(0)
        unanswered_question: UnansweredQuestion = UnansweredQuestion(question=query)
        minimal_search_result: MinimalSearchResults = search_engine(
            unanswered_question, k
        )
        for source in minimal_search_result.retrieved_sources:
            Logger.info(
                f"{source.file_path}"
                + f" [{source.first_character_index}:{source.last_character_index}]",
                "SEARCH",
            )

    def search_dataset(
        self, dataset_path: str = DATASET_PATH, k: int = 5, save_direcotry: str = ""
    ) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                "SEARCH_DATASET",
            )
            sys.exit(0)

    def answer(self, query: str, k: int = 5) -> None:
        pass

    def __load_unanswerd_question(self) -> RagDataset:
        unanswered_questions: RagDataset
        with open(CODE_BASE_QUESTIONS, "r") as unanswed_question_file:
            unanswered_questions = RagDataset.model_validate_json(
                unanswed_question_file.read()
            )
        return unanswered_questions

    def recall(self, student_search_result: str, data_set_path: str) -> None:
        pass
