"""
Rage Against Machine - Retrieval-Augmented Generation (RAG) System.

This module provides the main interface for interacting with the RAG
system built around the vLLM 0.10.1 codebase and documentation.

It exposes the RageAgainstMachine class, which coordinates indexing,
document retrieval, answer generation, dataset processing, and
retrieval evaluation.

The system supports both standard and hybrid retrieval strategies.

Configuration:
    CORPUS_PATH: Source corpus directory.
    CODE_BASE_QUESTIONS: Public code-related questions dataset.
    DOC_BASE_QUESTIONS: Public documentation-related questions dataset.
    DATASET_PATH: Directory containing evaluation datasets.
    STUDENT_SEARCH_RESULTS_PATH: Student retrieval results file.
    SAVE_DIRECTORY: Directory for storing search results.
    DATA_PROCESSED_PATH: Directory for processed corpus data.
    MAX_CHUNK_SIZE: Default maximum document chunk size.
"""

import sys
import os
from pathlib import Path

from src.core.utils import Logger, Stage, permission_checker
from src.core.validation_models import StudentSearchResultsAndAnswer


CORPUS_PATH = "data/raw/vllm-0.10.1"

CODE_BASE_QUESTIONS = (
    "data/public/UnansweredQuestions/dataset_code_public.json"
)

DOC_BASE_QUESTIONS = (
    "data/public/UnansweredQuestions/dataset_docs_public.json"
)

DATASET_PATH = "data/datasets/UnansweredQuestions"

STUDENT_SEARCH_RESULTS_PATH = (
    "data/datasets/UnansweredQuestions/dataset_docs_public.json"
)

SAVE_DIRECTORY = "data/output/search_results/UnansweredQuestions"

DATA_PROCESSED_PATH = "data/processed/"

MAX_CHUNK_SIZE = 2000


class RageAgainstMachine:
    """
    Main interface for interacting with the RAG application.

    This class provides high-level operations for indexing a corpus,
    searching documents, generating answers, processing datasets,
    and evaluating retrieval performance.

    It delegates the actual processing operations to specialized
    components within the core package.

    Supported operations:
        - Indexing the source corpus.
        - Searching for relevant documents.
        - Searching evaluation datasets.
        - Generating answers from retrieved context.
        - Generating answers for datasets.
        - Evaluating retrieval performance using Recall@K.

    Retrieval can be performed using standard or hybrid strategies.
    """

    def index(
        self, max_chunk_size: int = MAX_CHUNK_SIZE, hybrid: str = "false"
    ) -> None:
        """
        Index the source corpus and build the retrieval index.

        Args:
            max_chunk_size: Maximum number of characters allowed
                in a document chunk. Defaults to MAX_CHUNK_SIZE.
            hybrid: Whether to enable hybrid retrieval indexing.
                Accepted values are "true" and "false".

        Returns:
            None.

        Raises:
            SystemExit: If validation or indexing fails.
        """
        is_hybrid = self.__check_hybrid(hybrid, Stage.INDEXING)

        if not 400 < max_chunk_size <= 2000:
            Logger.error(
                "max chunk size must not be under of 400 or greater than 5000",
                "INDEXING",
            )
            sys.exit(1)

        from src.core.indexer import indexer, IndexerError

        try:
            indexer(
                corpus_path=CORPUS_PATH,
                max_chunk_size=max_chunk_size,
                is_hybrid=is_hybrid,
            )
        except IndexerError as error:
            Logger.error(str(error), "INDEXING")
            sys.exit(1)
        except Exception as error:
            Logger.error(str(error), "INDEXING")
            sys.exit(1)

    def search_dataset(
        self,
        dataset_path: str = DATASET_PATH,
        save_directory: str = "",
        k: int = 5,
        hybrid: str = "false",
    ) -> None:
        """
        Execute document retrieval for every question in a dataset.

        The retrieved documents for each question are saved to the
        specified output file or directory.

        Args:
            dataset_path: Path to the dataset containing questions.
            save_directory: Destination path for the retrieval results.
            k: Maximum number of documents to retrieve per question.
            hybrid: Whether to enable hybrid retrieval.
                Accepted values are "true" and "false".

        Returns:
            None.

        Raises:
            SystemExit: If validation, permission checking, or retrieval fails.
        """
        self.__validate_k(k, Stage.SEARCH_DATASET)

        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.SEARCH_DATASET)

        _ = permission_checker(
            file_path=dataset_path,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "SEARCH DATASET"),
        )

        self.__create_file_path_if_not_exist(save_directory)

        _ = permission_checker(
            file_path=save_directory,
            exist=True,
            write=True,
            fn=lambda message: Logger.error(message, "SEARCH DATASET"),
        )

        from src.core.question_manager import (
            question_manager,
            QuestionManagerError,
        )

        try:
            question_manager.search_datasets(
                dataset_path=dataset_path,
                top_k=k,
                save_directory=save_directory,
                is_hybrid=is_hybrid,
            )
        except QuestionManagerError as error:
            Logger.error(str(error), "SEARCH DATASET")
            sys.exit(1)

    def evaluate(
        self, student_search_results_path: str, dataset_path: str
    ) -> None:
        """
        Evaluate document retrieval performance using Recall@K.

        Compares the documents retrieved by the student implementation
        against the expected relevant documents in the reference dataset.

        Args:
            student_search_results_path: Path to the retrieved search
                results generated by the application.
            dataset_path: Path to the reference dataset containing
                the expected relevant documents.

        Returns:
            None. Evaluation statistics are logged.

        Raises:
            SystemExit: If the input files cannot be accessed or
                the evaluation process fails.
        """
        _ = permission_checker(
            file_path=student_search_results_path,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "RECALL@K"),
        )

        _ = permission_checker(
            file_path=dataset_path,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "RECALL@K"),
        )

        from src.core.recallk import recallk, RecallError, RecallStats

        try:
            recall_stats: RecallStats = recallk(
                student_search_results_path, dataset_path
            )
            Logger.info(str(recall_stats), "RECALL@K")

        except RecallError as error:
            Logger.error(str(error), "RECALL@k")
            sys.exit(1)

    def search(self, query: str, k: int, hybrid: str = "false") -> None:
        """
        Retrieve the most relevant documents for a given query.

        Args:
            query: User question or search query.
            k: Maximum number of documents to retrieve.
            hybrid: Whether to enable hybrid retrieval.
                Accepted values are "true" and "false".

        Returns:
            None. Retrieved document paths and character positions
            are printed to standard output.

        Raises:
            SystemExit: If the query is empty, validation fails,
                or document retrieval encounters an error.
        """
        self.__validate_k(k, Stage.SEARCH)

        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)

        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.SEARCH)

        from src.core.question_manager import (
            question_manager,
            QuestionManagerError,
        )

        try:
            minimal_search_results = question_manager.search(
                query, k, is_hybrid
            )

        except QuestionManagerError as error:
            Logger.error(str(error), "SEARCH")
            sys.exit(1)

        except Exception as error:
            Logger.error(str(error), "SEARCH")
            sys.exit(1)

        Logger.info(f"Query: {query}", "SEARCH")
        Logger.info("RETRIEVED_DOCUMENTS: ", "SEARCH")

        for document in minimal_search_results.retrieved_sources:
            print(
                document.file_path,
                f"[{document.first_character_index}:"
                + f"{document.last_character_index}]",
            )

    def answer(self, query: str, k: int, hybrid: str = "false") -> None:
        """
        Generate an answer using the retrieved document context.

        Args:
            query: User question to answer.
            k: Maximum number of documents to retrieve as context.
            hybrid: Whether to enable hybrid retrieval.
                Accepted values are "true" and "false".

        Returns:
            None. The generated answer is logged.

        Raises:
            SystemExit: If the query is empty, validation fails,
                or answer generation encounters an error.
        """
        self.__validate_k(k, Stage.ANSWER)

        is_hybrid: bool = self.__check_hybrid(hybrid, Stage.ANSWER)

        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)

        from src.core.answer_manager import answer_manager, AnswerError

        try:
            answer: str = answer_manager.answer(query, k, is_hybrid)
            Logger.info(answer, "ANSWER")

        except AnswerError as error:
            Logger.error(str(error), "ANSWER")
            sys.exit(1)

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str
    ) -> None:
        """
        Generate answers for questions with previously retrieved documents.

        Reads the student search results, generates an answer for each
        question using its retrieved context, and saves the resulting
        questions, documents, and answers to a JSON file.

        Args:
            student_search_results_path: Path to the JSON file containing
                questions and their retrieved documents.
            save_directory: Destination file path for the generated
                question-answer results.

        Returns:
            None.

        Raises:
            SystemExit: If file permissions are invalid or answer
                generation or serialization fails.
        """
        _ = permission_checker(
            file_path=student_search_results_path,
            exist=True,
            read=True,
            fn=lambda message: Logger.error(message, "ANSWER DATASET"),
        )

        self.__create_file_path_if_not_exist(save_directory)

        _ = permission_checker(
            file_path=save_directory,
            exist=True,
            write=True,
            fn=lambda message: Logger.error(message, "ANSWER DATASET"),
        )

        from src.core.answer_manager import answer_manager, AnswerError

        try:
            student_search_results_and_answer: (
                StudentSearchResultsAndAnswer
            ) = answer_manager.answer_dataset(student_search_results_path)

            with open(save_directory, "w") as save_file:
                _ = save_file.write(
                    student_search_results_and_answer.model_dump_json(indent=4)
                )

        except AnswerError as error:
            Logger.error(str(error), "ANSWER DATASET")
            sys.exit(1)

        except Exception as error:
            Logger.error(str(error), "ANSWER DATASET")
            sys.exit(1)

    def __check_hybrid(self, hybrid: str, stage: Stage) -> bool:
        """
        Validate and convert the hybrid retrieval configuration.

        Args:
            hybrid: String representation of the hybrid configuration.
                Accepted values are "true" and "false".
            stage: Application stage used to identify the source of
                validation errors in the logs.

        Returns:
            bool: True if hybrid retrieval is enabled, otherwise False.

        Raises:
            SystemExit: If the supplied value is invalid.
        """
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}.: "
                + "allowed values: true, false",
                stage.name,
            )
            sys.exit(1)

        return hybrid == "true"

    def __validate_k(self, k: int, stage: Stage) -> None:
        """
        Validate the requested number of retrieved documents.

        Args:
            k: Number of documents requested.
            stage: Application stage used to identify validation errors.

        Returns:
            None.

        Raises:
            SystemExit: If k is less than or equal to zero or greater than 10.
        """
        if k <= 0 or k > 10:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                stage.name,
            )
            sys.exit(1)

    def __create_file_path_if_not_exist(self, file_path: str) -> None:
        """
        Create a destination file and its parent directories if necessary.

        If the specified path does not exist, its parent directories
        are created and an empty file is initialized.

        Args:
            file_path: Destination file path.

        Returns:
            None.
        """
        if not os.access(file_path, os.F_OK):
            save_directory_path: Path = Path(file_path)
            save_directory_path.parent.mkdir(parents=True, exist_ok=True)
            save_directory_path.touch()
