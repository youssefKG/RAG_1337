from pydantic import ValidationError
from src.core.config_manager import ConfigManager, config_manager
from src.core.search_engine import SearchEngine, SearchType, search_engine
from src.core.validation_models import (
    RagDataset,
    StudentSearchResults,
    MinimalSearchResults,
    UnansweredQuestion,
)
from tqdm import tqdm
from src.server.repositories import transaction_atomic
from src.server.errors import CustomDatabaseError
from src.core.utils import Logger, permission_checker


class QuestionManagerError(Exception):
    """Raised when a question management operation fails."""


class QuestionManager:
    """Manage question retrieval and dataset search operations.

    Provides interfaces for searching individual questions and evaluating
    retrieval performance against a dataset.
    """

    def __init__(
        self, *, search_engine: SearchEngine, config_manager: ConfigManager
    ) -> None:
        """Initialize the question manager.

        Args:
            search_engine: Engine responsible for retrieving relevant documents.
            config_manager: Manager providing indexing and search configuration.
        """
        self.__search_engine: SearchEngine = search_engine
        self.__config_manager: ConfigManager = ConfigManager()

    def search_datasets(
        self,
        *,
        dataset_path: str,
        save_directory: str,
        top_k: int,
        is_hybrid: bool,
    ) -> None:
        """Evaluate document retrieval against a RAG question dataset.

        Loads a dataset, retrieves relevant documents for each question,
        and saves the aggregated retrieval results as JSON.

        Args:
            dataset_path: Path to the input RAG dataset.
            save_directory: Destination path for the search results JSON file.
            top_k: Maximum number of documents retrieved per question.
            is_hybrid: Whether to use hybrid retrieval instead of lexical retrieval.

        Raises:
            QuestionManagerError: If dataset processing, retrieval, or
                result serialization fails.
        """
        self.__check_preindexing_strategy(is_hybrid)
        rag_data_set: RagDataset = self.__load_rag_dataset(dataset_path)
        search_results: list[MinimalSearchResults] = list()
        search_type: SearchType = (
            SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        )
        try:
            with transaction_atomic():
                for question in tqdm(
                    rag_data_set.rag_questions, desc="Retrieval"
                ):
                    minimal_search_result: MinimalSearchResults = (
                        self.__search_engine(
                            unanswered_question=question,
                            top_k=top_k,
                            search_type=search_type,
                        )
                    )
                    search_results.append(minimal_search_result)
            student_search_results: StudentSearchResults = (
                StudentSearchResults(search_results=search_results, k=top_k)
            )
            _ = permission_checker(
                file_path=save_directory,
                exist=True,
                write=True,
                fn=lambda message: Logger.error(message, "SEARCH DATASETS"),
            )
            with open(save_directory, "w") as save_file:
                _ = save_file.write(
                    student_search_results.model_dump_json(indent=4)
                )
        except CustomDatabaseError as error:
            raise QuestionManagerError(
                "DATABASE ERROR: " 
                + str(error)
            ) from error
        except Exception as error:
            raise QuestionManagerError(str(error)) from error

    def __load_rag_dataset(self, file_path: str) -> RagDataset:
        """Load and validate a RAG dataset from a JSON file.

        Args:
            file_path: Path to the JSON dataset.

        Returns:
            The validated RAG dataset.

        Raises:
            QuestionManagerError: If the dataset does not conform to the
                expected schema.
        """
        with open(file_path, "r") as file:
            try:
                rag_dataset: RagDataset = RagDataset.model_validate_json(
                    file.read()
                )
                return rag_dataset
            except ValidationError as error:
                raise QuestionManagerError(error.errors()[0]["msg"])

    def search(
        self, query: str, top_k: int, is_hybrid: bool
    ) -> MinimalSearchResults:
        """Retrieve documents relevant to an individual question.

        Args:
            query: User's search query.
            top_k: Maximum number of documents to retrieve.
            is_hybrid: Whether to use hybrid retrieval instead of lexical retrieval.

        Returns:
            Search results containing the most relevant documents.

        Raises:
            QuestionManagerError: If the configured indexing strategy does
                not support the requested retrieval method.
        """
        self.__check_preindexing_strategy(is_hybrid)
        question: UnansweredQuestion = UnansweredQuestion(question=query)
        search_type: SearchType = (
            SearchType.HYBRID if is_hybrid else SearchType.LEXICAL
        )
        minimal_search_results: MinimalSearchResults = self.__search_engine(
            unanswered_question=question, top_k=top_k, search_type=search_type
        )
        return minimal_search_results

    def __check_preindexing_strategy(self, is_hybrid: bool) -> None:
        """Validate the requested search method against the indexing strategy.

        Args:
            is_hybrid: Whether hybrid retrieval is requested.

        Raises:
            QuestionManagerError: If indexing is unavailable or the
                requested retrieval method is incompatible with the
                existing index.
        """
        preindexing_strategy: str = (
            self.__config_manager.config.indexing_strategy
        )
        if preindexing_strategy == "none":
            # TODO: Throw exception for the server instead of exit
            raise QuestionManagerError(
                "search cannot performed because no indexing is available"
            )
        elif preindexing_strategy == "lexical" and is_hybrid:
            raise QuestionManagerError(
                "Hybrid search is not supported because your"
                + f" pre-indexing method is {preindexing_strategy}."
            )


question_manager: QuestionManager = QuestionManager(
    search_engine=search_engine, config_manager=config_manager
)

__all__ = ["QuestionManager", "question_manager"]
