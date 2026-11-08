"""Recall@K evaluation module for assessing RAG retrieval performance.

This module provides functionality to evaluate student search results
against a ground-truth dataset using Recall@1, Recall@3, Recall@5,
and Recall@10 metrics.
"""

from typing import override
from typing_extensions import Self
from pydantic import ValidationError, BaseModel
from dataclasses import dataclass

from src.core.utils import get_validation_error_message
from src.core.validation_models import (
    StudentSearchResults,
    AnsweredQuestion,
    MinimalSearchResults,
    MinimalSource,
)


class AnsweredQuestionGroundTruth(AnsweredQuestion):
    """Represent a ground-truth question with evaluation metadata.

    Attributes:
        difficulty: Difficulty level associated with the question.
        is_valid: Whether the question should be included in evaluation.
    """

    difficulty: str
    is_valid: bool


class GroundTruthModel(BaseModel):
    """Represent the validated ground-truth evaluation dataset.

    Attributes:
        rag_questions: List of ground-truth questions and their expected
            relevant sources.
    """

    rag_questions: list[AnsweredQuestionGroundTruth]


class RecallError(Exception):
    """Represent errors occurring during Recall@K evaluation."""


@dataclass
class RecallStats:
    """Store Recall@K evaluation metrics.

    Attributes:
        recall_1: Average recall among the first retrieved result.
        recall_3: Average recall among the first three retrieved results.
        recall_5: Average recall among the first five retrieved results.
        recall_10: Average recall among the first ten retrieved results.
    """

    recall_1: float
    recall_3: float
    recall_5: float
    recall_10: float

    @override
    def __str__(self) -> str:
        """Return a formatted representation of the recall metrics.

        Returns:
            A string containing recall values and their percentages.
        """
        return (
            f"\nRecall@1:  {self.recall_1:.4f} "
            f"({self.recall_1 * 100:.1f}%)\n"
            f"Recall@3:  {self.recall_3:.4f} "
            f"({self.recall_3 * 100:.1f}%)\n"
            f"Recall@5:  {self.recall_5:.4f} "
            f"({self.recall_5 * 100:.1f}%)\n"
            f"Recall@10: {self.recall_10:.4f} "
            f"({self.recall_10 * 100:.1f}%)"
        )

    def __add__(self, recall: object) -> Self:
        """Add another RecallStats instance to the current statistics.

        Args:
            recall: Statistics to accumulate into the current instance.

        Returns:
            The updated current RecallStats instance.

        Note:
            This operation modifies the current instance in place.
            Objects that are not RecallStats instances are ignored.
        """
        if isinstance(recall, RecallStats):
            self.recall_1 += recall.recall_1
            self.recall_3 += recall.recall_3
            self.recall_5 += recall.recall_5
            self.recall_10 += recall.recall_10
        return self

    def __truediv__(self, value: int) -> Self:
        """Divide all recall metrics by the provided value.

        Args:
            value: Divisor used to calculate average recall values.

        Returns:
            The updated current RecallStats instance.

        Note:
            This operation modifies the current instance in place.
        """
        self.recall_1 /= value
        self.recall_3 /= value
        self.recall_5 /= value
        self.recall_10 /= value
        return self


class RecallK:
    """Evaluate retrieval performance using Recall@K metrics.

    The evaluator compares retrieved sources against ground-truth
    relevant sources for each valid question and calculates the
    average Recall@1, Recall@3, Recall@5, and Recall@10.
    """

    def __call__(
        self,
        student_search_results_path: str,
        dataset_path: str
    ) -> RecallStats:
        """Evaluate student search results against a ground-truth dataset.

        Load and validate both input files, match questions using their
        identifiers, evaluate retrieved sources, and calculate average
        Recall@K metrics across all valid ground-truth questions.

        Args:
            student_search_results_path: Path to the student's search
                results JSON file.
            dataset_path: Path to the ground-truth dataset JSON file.

        Returns:
            RecallStats containing the average Recall@1, Recall@3,
            Recall@5, and Recall@10 values.

        Raises:
            RecallError: If the input files are invalid, question IDs
                are duplicated, questions are missing or mismatched,
                or no valid ground-truth questions are available.
        """
        total_stats: RecallStats = RecallStats(
            recall_1=0.0,
            recall_3=0.0,
            recall_5=0.0,
            recall_10=0.0,
        )

        ground_truth: GroundTruthModel = (
            self.__load_and_validate_dataset_path(dataset_path)
        )

        student_results: StudentSearchResults = (
            self.__load_and_validate_student_search_results(
                student_search_results_path
            )
        )

        ground_truth_questions: dict[str, AnsweredQuestionGroundTruth] = {
            question.question_id: question
            for question in ground_truth.rag_questions
            if question.is_valid
        }

        student_questions: dict[str, MinimalSearchResults] = {
            question.question_id: question
            for question in student_results.search_results
        }

        if len(student_questions) != len(student_results.search_results):
            raise RecallError(
                "Duplicate question IDs found in student search results."
            )

        missing_questions: set[str] = (
            ground_truth_questions.keys() - student_questions.keys()
        )

        if missing_questions:
            raise RecallError(
                "Some ground-truth questions are missing from "
                + "student search results: "
                + ", ".join(missing_questions)
            )

        question_count: int = len(ground_truth_questions)

        if question_count == 0:
            raise RecallError(
                "No valid ground-truth questions available for evaluation."
            )

        for question_id, truth_question in ground_truth_questions.items():

            student_question: MinimalSearchResults = (
                student_questions[question_id]
            )

            if student_question.question != truth_question.question:
                raise RecallError(
                    f"Question mismatch for ID {question_id}."
                )

            question_stats: RecallStats = (
                self.__evaluate_student_question_search_against_ground_truth(
                    student_question,
                    truth_question,
                )
            )

            total_stats += question_stats

        total_stats /= question_count

        return total_stats

    def __sources_overlap(
        self,
        retrieved_source: MinimalSource,
        relevant_source: MinimalSource,
    ) -> bool:
        """Determine whether two source character ranges overlap.

        Two sources overlap when they reference the same file and their
        character intervals intersect.

        Args:
            retrieved_source: Source retrieved by the student search.
            relevant_source: Ground-truth relevant source.

        Returns:
            True if both sources belong to the same file and their
            character ranges overlap; otherwise, False.
        """
        return (
            retrieved_source.file_path == relevant_source.file_path
            and retrieved_source.first_character_index
            < relevant_source.last_character_index
            and relevant_source.first_character_index
            < retrieved_source.last_character_index
        )

    def __evaluate_student_question_search_against_ground_truth(
        self,
        student_question: MinimalSearchResults,
        truth_question: AnsweredQuestionGroundTruth,
    ) -> RecallStats:
        """Evaluate retrieval performance for a single question.

        Calculate Recall@1, Recall@3, Recall@5, and Recall@10 by checking
        how many ground-truth relevant sources overlap with at least
        one of the top-K retrieved sources.

        Args:
            student_question: Student search results for the question.
            truth_question: Ground-truth question and relevant sources.

        Returns:
            RecallStats containing the recall metrics for this question.

        Raises:
            RecallError: If the ground-truth question contains no
                relevant sources.
        """
        relevant_sources: list[MinimalSource] = list([
            source for source in truth_question.sources
        ])

        if not relevant_sources:
            raise RecallError(
                f"No relevant sources found for question "
                + f"{truth_question.question_id}."
            )

        retrieved_sources: list[MinimalSource] = (
            student_question.retrieved_sources
        )

        def calculate_recall_at_k(k: int) -> float:
            """Calculate recall among the top-K retrieved sources.

            Args:
                k: Number of top retrieved sources to evaluate.

            Returns:
                Fraction of ground-truth relevant sources retrieved
                within the top-K results.
            """
            retrieved_top_k: list[MinimalSource] = (
                retrieved_sources[:k]
            )

            hits: int = sum(
                any(
                    self.__sources_overlap(retrieved, relevant)
                    for retrieved in retrieved_top_k
                )
                for relevant in relevant_sources
            )

            return hits / len(relevant_sources)

        return RecallStats(
            recall_1=calculate_recall_at_k(1),
            recall_3=calculate_recall_at_k(3),
            recall_5=calculate_recall_at_k(5),
            recall_10=calculate_recall_at_k(10),
        )

    def __load_and_validate_dataset_path(
        self,
        dataset_path: str
    ) -> GroundTruthModel:
        """Load and validate the ground-truth dataset JSON file.

        Args:
            dataset_path: Path to the ground-truth dataset.

        Returns:
            A validated GroundTruthModel instance.

        Raises:
            RecallError: If the file cannot be read or its contents
                fail Pydantic validation.
        """
        try:
            with open(dataset_path, "r") as file:
                return GroundTruthModel.model_validate_json(file.read())

        except ValidationError as error:
            raise RecallError(
                get_validation_error_message(error, dataset_path)
            ) from error

        except Exception as error:
            raise RecallError(str(error)) from error

    def __load_and_validate_student_search_results(
        self,
        student_search_results_path: str
    ) -> StudentSearchResults:
        """Load and validate the student search results JSON file.

        Args:
            student_search_results_path: Path to the student's search
                results JSON file.

        Returns:
            A validated StudentSearchResults instance.

        Raises:
            RecallError: If the file cannot be read or its contents
                fail Pydantic validation.
        """
        try:
            with open(student_search_results_path, "r") as file:
                return StudentSearchResults.model_validate_json(
                    file.read()
                )

        except ValidationError as error:
            raise RecallError(
                get_validation_error_message(
                    error,
                    student_search_results_path
                )
            ) from error

        except Exception as error:
            raise RecallError(str(error)) from error


recallk: RecallK = RecallK()

__all__ = ["recallk", "RecallError", "RecallStats"]
