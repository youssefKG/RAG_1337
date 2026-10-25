import sys
import os
from pathlib import Path

from src.core.utils import Logger, Stage, permission_checker

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
    def index(self, max_chunk_size: int = MAX_CHUNK_SIZE, hybrid: str = "false") -> None:
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                 Stage.INDEXING.name
            )
            sys.exit(1)
        is_indexing_hybrid: bool = True if hybrid == "true" else False
        from src.core.indexer import indexer
        indexer(
            corpus_path=CORPUS_PATH,
            max_chunk_size=max_chunk_size,
            is_hybrid=is_indexing_hybrid
        )

    def search_dataset(
        self,
        dataset_path: str = DATASET_PATH,
        save_directory: str = "",
        k: int = 5,
        hybrid: str="false"
    ) -> None:
        self.__validate_k(k, Stage.SEARCH_DATASET)
        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.SEARCH_DATASET)
        _ = permission_checker(
                file_path=dataset_path,
                exist=True,
                read=True,
                fn=lambda message: Logger.error(message, "SEARCH DATASET")
           )
        self.__create_file_path_if_not_exist(save_directory)
        _ = permission_checker(
                file_path=save_directory,
                exist=True,
                write=True,
                fn=lambda message: Logger.error(message, "SEARCH DATASET")
           )
        from src.core.question_manager import question_manager, QuestionManagerError
        try:
            question_manager.search_datasets(
                dataset_path=dataset_path,
                top_k=k,
                save_directory=save_directory,
                is_hybrid=is_hybrid
            )
        except QuestionManagerError as error:
            Logger.error(str(error), "SEARCH DATASET")
            sys.exit(1)

    def search(self, query: str, k: int, hybrid: str="false") -> None:
        self.__validate_k(k, Stage.SEARCH)
        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)

        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.SEARCH)
        from src.core.question_manager import question_manager, QuestionManagerError
        try:
            minimal_search_results = question_manager.search(query, k, is_hybrid)
        except QuestionManagerError as error:
            Logger.error(str(error), "SEARCH")
            sys.exit(1)
        for document in minimal_search_results.retrieved_sources:
            print(
                document.file_path,
                f"[{document.first_character_index}:{document.last_character_index}]"
            )

    def answer(self, query: str, k: int, hybrid: str="false") -> None:
        self.__validate_k(k, Stage.ANSWER)
        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.ANSWER)
        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)
        from src.core.answer_manager import answer_manager, AnswerError
        try:
            answer: str = answer_manager.answer(query, k, is_hybrid)
            Logger.info(answer, "ANSWER")
        except  AnswerError as error:
            Logger.error(str(error), "ANSWER")
            sys.exit(1)

    def answer_dataset(self, student_search_results: str, save_directory: str, hybrid: str) -> None:
        _ = permission_checker(
                file_path=student_search_results,
                exist=True,
                read=True,
                fn=lambda message: Logger.error(message, "ANSWER DATASET")
            )
        self.__create_file_path_if_not_exist(save_directory)
        _ = permission_checker(
                file_path=save_directory,
                exist=True,
                write=True,
                fn=lambda message: Logger.error(message, "ANSWER DATASET")
            )
        from src.core.answer_manager import AnswerManager, AnswerError
        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.ANSWER_DATASET)
        try:
            pass
        except AnswerError as error:
            Logger.error(str(error), "ANSWER DATASET")

    def __check_hybrid(self, hybrid: str, stage: Stage) -> bool:
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                stage.name
            )
        return hybrid == "true"

    def __validate_k(self, k: int, stage: Stage) -> None:
        if k <= 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                stage.name
            )
            sys.exit(0)

    def __create_file_path_if_not_exist(self, file_path: str) -> None:
        if not os.access(file_path, os.F_OK):
            save_directory_path: Path = Path(file_path)
            save_directory_path.parent.mkdir(parents=True, exist_ok=True)
            save_directory_path.touch()
