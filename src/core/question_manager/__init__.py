import os
import sys
from typing import Literal
from pydantic import ValidationError
from pathlib import Path
from src.server.repositories import QuestionRepositoryInterface, question_repository
from src.core.config_manager import ConfigModel, ConfigManager, config_manager
from src.core.utils import permission_checker, Logger
from src.core.search_engine import SearchEngine, SearchType, search_engine
from src.core.validation_models import RagDataset, StudentSearchResults, MinimalSearchResults, UnansweredQuestion
from tqdm import tqdm

class QuestionManager:
    def __init__(
        self,
        *,
        question_repository: QuestionRepositoryInterface,
        search_engine: SearchEngine,
        config_manager: ConfigManager
     ) -> None:
        self.__question_repository: QuestionRepositoryInterface = question_repository
        self.__search_engine: SearchEngine = search_engine
        self.__config_manager: ConfigManager = ConfigManager()

    def search_datasets(
        self,
        *,
        dataset_path: str,
        save_directory: str,
        top_k: int,
        is_hybrid: bool
    ) -> None:
        permission_checker(
            file_path=dataset_path,
            exist=True,
            write=True,
            fn=lambda message: Logger.error(message, "SEARCH DATASET")
        )
        if not os.access(save_directory, os.F_OK):
            save_directory_path: Path = Path(save_directory)
            save_directory_path.parent.mkdir(parents=True, exist_ok=True)
            save_directory_path.touch()
        permission_checker(
            file_path=save_directory,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "SEARCH DATASET")
        )
        config: ConfigModel = self.__config_manager.config
        indexing_strategy: Literal["lexical", "hybrid", "none"] = config.indexing_strategy
        if indexing_strategy == "none":
            # TODO: raise exception instead of exit for the server
            Logger.error(
                "Search cannot be performed because no indexing is available.",
                 "SEARCH DATASET"
             )
            return
        elif indexing_strategy != "hybrid" and is_hybrid:
            # TODO: raise exception instead of exit for the server
            Logger.error(
                f"Hybrid search is not supported because your pre-indexing method is {indexing_strategy}.",
                "SEARCH DATASET"
            )
            return
        rag_data_set: RagDataset = self.__load_rag_dataset(dataset_path)
        search_results: list[MinimalSearchResults] = list()
        search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        for question in tqdm(rag_data_set.rag_questions, desc="Retrieval"):
            minimal_search_result: MinimalSearchResults = self.__search_engine(
                question=question,
                top_k=top_k,
                search_type=search_type
            )
            search_results.append(minimal_search_result)
        student_search_results: StudentSearchResults = StudentSearchResults(
            search_results=search_results,
            k=top_k
        )
        with open(save_directory, "w") as save_file:
            _ = save_file.write(student_search_results.model_dump_json(indent=4))

    def __load_rag_dataset(self, file_path: str) -> RagDataset:
        permission_checker(
            file_path=file_path,
            read=True,
            exist=True,
            fn= lambda message: Logger.error(message, "SEARCH DATASET")
        )
        with open(file_path, "r") as file:
            try:
                rag_dataset: RagDataset = RagDataset.model_validate_json(file.read())
                return rag_dataset
            except ValidationError as error:
                Logger.error(error.errors()[0]["msg"], "SEARCH DATASET")
                sys.exit(1)

    def search(self, query: str, top_k: int, is_hybrid: bool) -> MinimalSearchResults:
        preindexing_strategy: str = self.__config_manager.config.indexing_strategy
        if preindexing_strategy == "none":
            # TODO: Throw exception for the server instead of exit
            Logger.error(
                "search cannot performed because no indexing is available",
                "SEARCH"
            )
            sys.exit(1)
        elif preindexing_strategy == "hybrid" and is_hybrid:
            Logger.error(
                f"Hybrid search is not supported because your pre-indexing method is {preindexing_strategy}.",
                 "SEARCH"
            )
            sys.exit(1)
        question: UnansweredQuestion = UnansweredQuestion(question=query)
        search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        minimal_search_results: MinimalSearchResults = self.__search_engine(
            question=question,
            top_k=top_k,
            search_type=search_type
        )
        return minimal_search_results

question_manager: QuestionManager = QuestionManager(
    question_repository=question_repository,
    search_engine=search_engine,
    config_manager=config_manager
)

__all__ = [
    "QuestionManager",
    "question_manager"
]
