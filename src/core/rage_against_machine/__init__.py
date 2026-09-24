import sys
import os
from src.core.search_engine import SearchEngine, search_engine
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    RagDataset,
    MinimalSource,
    StudentSearchResults
)
from src.core.utils.logger import Logger
from src.core.indexer import indexer, Indexer
from pydantic import RootModel, ValidationError
from pathlib import Path


CORPUS_PATH = "data/raw/vllm-0.10.1"
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"
DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"
DATASET_PATH = "data/datasets/UnansweredQuestions/"
STUDENT_SEARCH_RESULTS_PATH = (
    "data/datasets/UnansweredQuestions/dataset_docs_public.json"
)
SAVE_DIRECTORY = "data/output/search_results/UnansweredQuestions"

DATA_PROCESSED_PATH = "data/processed/index.json"
MAX_CHUNK_SIZE = 2000


class RageAgainstMachine:
    def __init__(self) -> None:
        self.__search_engine: SearchEngine = search_engine
        self.__indexer: Indexer = indexer

    def index(self, max_chunk_size: int = MAX_CHUNK_SIZE) -> None:
        minimal_sources: str = (
                RootModel[list[MinimalSource]](
                    self.__indexer(
                        corpus_path=CORPUS_PATH,
                        max_chunk_size=max_chunk_size
                        )
                    )
                ).model_dump_json(indent=4)
        try:
            index_path = Path(DATA_PROCESSED_PATH)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.touch()
            with index_path.open("w") as file:
                _ =file.write(minimal_sources)
        except PermissionError:
            Logger.error(
                    f"Permision Error cannot write to file {DATA_PROCESSED_PATH + 'index.json'}",
                    "INDEXING"
                    )
            sys.exit(1)
        except Exception as error:
            Logger.error(str(error), "INDEXING")
            sys.exit(1)


    def search(self, query: str, k: int = 5) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                "SEARCH_DATASET",
            )
            sys.exit(1)
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
        self, dataset_path: str = DATASET_PATH, k: int = 5, save_directory: str = ""
    ) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                "SEARCH_DATASET",
            )
            sys.exit(0)
        unanswered_questions: RagDataset = self.__load_unanswered_questions(dataset_path)
        save_directory_path = Path(save_directory)
        save_directory_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with save_directory_path.open() as file:
                pass
        except PermissionError:
            Logger.error(
                    f"Permision Error cannot write to file {save_directory}",
                    "SEARCH"
                    )
            sys.exit(1)
        except Exception as error:
            Logger.error(str(error), "SEARCH")
            sys.exit(1)

            

    def answer(self, query: str, k: int = 5) -> None:
        pass

    def __load_unanswered_questions(self, dataset_path: str) -> RagDataset:
        self.__check_is_exist(dataset_path, "SEARCH")
        self.__check_read_permision(dataset_path, "SEARCH")
        unanswered_questions: RagDataset
        try:
            with open(CODE_BASE_QUESTIONS, "r") as unanswed_question_file:
                unanswered_questions = RagDataset.model_validate_json(
                    unanswed_question_file.read()
                )
            return unanswered_questions
        except ValidationError as errors:
            print(errors)
            sys.exit(1)

    def __get_search_results(self, dataset: RagDataset, top_k: int) -> StudentSearchResults:
        search_results: list[MinimalSearchResults] = list()
        for question in dataset.rag_questions:
            minimal_search_result: MinimalSearchResults = self.__search_engine(question, top_k)
            search_results.append(minimal_search_result)
        return StudentSearchResults(search_results=search_results, k=top_k)

    def __check_write_permision(self, file_path: str, stage: str) -> None:
        if not os.access(file_path, os.W_OK):
            Logger.error("Permission denied: cannot write to '{file_path}'", stage)
            sys.exit(2)

    def __check_read_permision(self, file_path: str, stage: str) -> None:
        if not os.access(file_path, os.R_OK):
            Logger.error("Permission denied: cannot write to '{file_path}'", stage)
            sys.exit(2)

    def __check_is_exist(self, file_path: str, stage: str) -> None:
        if not os.access(file_path, os.F_OK):
            Logger.error(f"File not found: unable to access '{file_path}'", stage)
            sys.exit(2)
