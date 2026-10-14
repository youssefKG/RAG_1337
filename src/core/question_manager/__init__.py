import sys
from typing import Literal
from pydantic import ValidationError
from src.core.entities import Document, QuestionAnswer
from src.server.repositories import QuestionRepositoryInterface
from src.core.config_manager import ConfigModel, ConfigManager
from src.core.utils import permission_checker, Logger
from src.core.search_engine import SearchEngine, SearchType
from src.core.validation_models import RagDataset, StudentSearchResults, MinimalSearchResults

class QuestionManager:
    def __init__(self, question_repository: QuestionRepositoryInterface, search_engine: SearchEngine, config_manager: ConfigManager) -> None:
        self.__question_repository: QuestionRepositoryInterface = question_repository
        self.__search_engine: SearchEngine = search_engine
        self.__config_manager: ConfigManager = ConfigManager()

    def search_datasets(
        self,
        data_set_path: str,
        save_directory: str,
        k: int,
        is_hybrid: bool
    ) -> None:
        permission_checker(
            file_path=data_set_path,
            exist=True,
            write=True,
            fn=lambda message: Logger.error(message, "SEARCH DATA_SET")
        )
        permission_checker(
            file_path=save_directory,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "SEARCH DATASET")
        )
        config: ConfigModel = self.__config_manager.config
        indexing_strategy: Literal["lexical", "hybrid", "none"] = config.indexing_strategy
        if indexing_strategy == "none":
            Logger.error("Search cannot be performed because no indexing is available.", "SEARCH DATASET")
            return
        elif indexing_strategy == "lexical" and is_hybrid:
            Logger.error(
                "Hybrid search is not supported because your pre-indexing method is lexical.",
                "SEARCH DATASET"
            )
            return
        rag_data_set: RagDataset = self.__load_rag_dataset(data_set_path)
        search_results: list[MinimalSearchResults] = list()
        search_type: SearchType = SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        for question in rag_data_set.rag_questions:
            search_results.append(self.__search_engine(
                question=question,
                top_k=k,
                search_type=search_type
            ))
        student_search_results: StudentSearchResults = StudentSearchResults(search_results=search_results, k=k)
        with open(save_directory, "w") as save_file:
            _ = save_file.write(student_search_results.model_dump_json(indent=4))

    def answer_question(self) -> None:
        pass

    def get_question_documents(self, question_id: str) -> list[Document]:
        return []

    def get_question_answer(self, question_id: str) -> QuestionAnswer | None:
        return None

    def create_question_answer(self, question_answer: QuestionAnswer) -> None:
        pass


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

