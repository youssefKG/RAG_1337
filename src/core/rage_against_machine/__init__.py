import sys

from src.core.search_engine import SearchEngine, search_engine
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    RagDataset,
    MinimalSource,
    StudentSearchResults
)
from src.core.utils import Logger, Stage, permission_checker
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
        index_path = Path(DATA_PROCESSED_PATH)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.touch()
        permission_checker(
            file_path=DATASET_PATH,
            exist=True,
            write=True,
            fn= lambda x: Logger.error(x, Stage.INDEXING.name)
        )
        with index_path.open("w") as file:
            _ =file.write(minimal_sources)


    def search(self, query: str, k: int = 5) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
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
                Stage.SEARCH.name
            )

    def search_dataset(
        self, dataset_path: str = DATASET_PATH, k: int = 5, save_directory: str = ""
    ) -> None:
        if k == 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(0)
        # load the unanswerd question from dataset path
        unanswered_questions: RagDataset = self.__load_unanswered_questions(dataset_path, Stage.SEARCH_DATASET)
        # get the student search result for the questions
        student_search_result: StudentSearchResults = self.__get_student_search_results(unanswered_questions, k)
        # create directory for save directory if is not exist
        save_directory_path = Path(save_directory)
        save_directory_path.parent.mkdir(parents=True, exist_ok=True)
        save_directory_path.touch()
        # check the write permission for save directory
        permission_checker(file_path=dataset_path, exist=True, write=True, fn= lambda x: Logger.error(x, Stage.SEARCH_DATASET.name))
        try:
            with save_directory_path.open("w") as file:
                _ = file.write(student_search_result.model_dump_json())
        except PermissionError:
            Logger.error(
                    f"Permision Error cannot write to file {save_directory}",
                    Stage.SEARCH.name
                    )
            sys.exit(1)
        except Exception as error:
            Logger.error(str(error), Stage.SEARCH.name)
            sys.exit(1)

    def answer(self, query: str, k: int = 5) -> None:
        pass

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
        for question in rag_dataset.rag_questions:
            minimal_search_result: MinimalSearchResults = self.__search_engine(question, top_k)
            search_results.append(minimal_search_result)
        return StudentSearchResults(search_results=search_results, k=top_k)
