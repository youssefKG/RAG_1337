import sys
import os
from pathlib import Path
from pydantic import  ValidationError
from tqdm import tqdm

from src.core.search_engine import SearchEngine, search_engine, SearchType
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    RagDataset,
    StudentSearchResults
)
from src.core.utils import Logger, Stage, permission_checker, INIT_DB
from src.core.indexer import indexer, Indexer


CORPUS_PATH = "data/raw/vllm-0.10.1"
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"
DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"
DATASET_PATH = "data/datasets/UnansweredQuestions"
STUDENT_SEARCH_RESULTS_PATH = (
    "data/datasets/UnansweredQuestions/dataset_docs_public.json"
)
SAVE_DIRECTORY = "data/output/search_results/UnansweredQuestions"

DATA_PROCESSED_PATH = "data/processed/"
MAX_CHUNK_SIZE = 2000


class RageAgainstMachine:
    def __init__(self) -> None:
        self.__search_engine: SearchEngine = search_engine
        self.__indexer: Indexer = indexer

    def index(self, max_chunk_size: int = MAX_CHUNK_SIZE, hybrid: str = "true") -> None:
        if max_chunk_size <= 200:
            Logger.error(
                f"Invalid max_chunk_size ({max_chunk_size}). "  
                + "The minimum allowed chunk size is 200 to maintain useful context.",
                Stage.INDEXING.name
            )
            sys.exit(1)
        self.__indexer(corpus_path=CORPUS_PATH, max_chunk_size=max_chunk_size)

    def search(self, query: str, k: int = 5, search_type: SearchType=SearchType.LEXICAL) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(1)
        unanswered_question: UnansweredQuestion = UnansweredQuestion(question=query)
        minimal_search_result: MinimalSearchResults = search_engine(
            unanswered_question, k, search_type
        )
        for source in minimal_search_result.retrieved_sources:
            Logger.info(
                f"{source.file_path}"
                + f" [{source.first_character_index}:{source.last_character_index}]",
                Stage.SEARCH.name
            )

    def search_dataset(
        self,
        dataset_path: str = DATASET_PATH,
        k: int = 5,
        save_directory: str = "",
    ) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(0)
        unanswered_questions: RagDataset = self.__load_unanswered_questions(dataset_path, Stage.SEARCH_DATASET)
        student_search_result: StudentSearchResults = self.__get_student_search_results(unanswered_questions, k)
        save_directory_path = self.__create_file(save_directory)
        permission_checker(
            file_path=dataset_path,
            exist=True,
            write=True,
            fn= lambda x: Logger.error(x, Stage.SEARCH_DATASET.name)
        )
        try:
            with save_directory_path.open("w") as file:
                _ = file.write(student_search_result.model_dump_json())
        except Exception as error:
            Logger.error(str(error), Stage.SEARCH.name)
            sys.exit(1)

    def __load_unanswered_questions(self, dataset_path: str, stage: Stage) -> RagDataset:
        # check if the dataset path is exist and read permission
        permission_checker(
            file_path=dataset_path,
            exist=True,
            read=True,
            fn=lambda x: Logger.error(x, stage.name)
        )
        unanswered_questions: RagDataset
        try:
            with open(CODE_BASE_QUESTIONS, "r") as unanswed_question_file:
                unanswered_questions = RagDataset.model_validate_json(
                    unanswed_question_file.read()
                )
            return unanswered_questions
        except ValidationError as errors:
            Logger.error(errors.errors()[0]["msg"], stage.name)
            sys.exit(1)

    def __get_student_search_results(self, rag_dataset: RagDataset, top_k: int) -> StudentSearchResults:
        search_results: list[MinimalSearchResults] = list()
        for question in tqdm(rag_dataset.rag_questions, total=len(rag_dataset.rag_questions)):
            minimal_search_result: MinimalSearchResults = self.__search_engine(question, top_k)
            search_results.append(minimal_search_result)
        return StudentSearchResults(search_results=search_results, k=top_k)

    def __create_file(self, file_path: str) -> Path:
        path = Path(file_path)
        if os.path.exists(file_path):
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path
