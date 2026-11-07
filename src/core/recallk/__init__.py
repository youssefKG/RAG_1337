from typing import override
from pydantic import ValidationError, BaseModel
from dataclasses import dataclass

from src.core.validation_models import (
    StudentSearchResults,
    AnsweredQuestion,
    MinimalSearchResults,
    MinimalSource,
)


class AnsweredQuestionGroundTruth(AnsweredQuestion):
    difficulty: str
    is_valid: bool


class GroundTruthModel(BaseModel):
    rag_questions: list[AnsweredQuestionGroundTruth]


class RecallError(Exception):
    ...


@dataclass
class RecallStats:
    recall_1: float
    recall_3: float
    recall_5: float
    recall_10: float

    @override
    def __str__(self) -> str:
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


class RecallK:

    def __call__(
        self, student_search_results_path: str, dataset_path: str
    ) -> RecallStats:

        ground_truth: GroundTruthModel = (
            self.__load_and_validate_dataset_path(dataset_path)
        )

        student_results: StudentSearchResults = (
            self.__load_and_validate_student_search_results(
                student_search_results_path
            )
        )

        if student_results.k < 10:
            raise RecallError(
                "Student search results must contain at least "
                + "10 retrieved sources to calculate Recall@10. "
                + f"Configured K: {student_results.k}."
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

        if len(ground_truth_questions) != sum(
            question.is_valid for question in ground_truth.rag_questions
        ):
            raise RecallError(
                "Duplicate question IDs found in ground-truth dataset."
            )

        missing_questions: set[str] = (
            ground_truth_questions.keys() - student_questions.keys()
        )

        if missing_questions:
            raise RecallError(
                "Some ground-truth questions are missing from "
                "student search results: "
                + ", ".join(missing_questions)
            )

        total_stats: RecallStats = RecallStats(
            recall_1=0.0,
            recall_3=0.0,
            recall_5=0.0,
            recall_10=0.0,
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

            total_stats.recall_1 += question_stats.recall_1
            total_stats.recall_3 += question_stats.recall_3
            total_stats.recall_5 += question_stats.recall_5
            total_stats.recall_10 += question_stats.recall_10

        return RecallStats(
            recall_1=total_stats.recall_1 / question_count,
            recall_3=total_stats.recall_3 / question_count,
            recall_5=total_stats.recall_5 / question_count,
            recall_10=total_stats.recall_10 / question_count,
        )

    @staticmethod
    def __sources_overlap(
        retrieved_source: MinimalSource,
        relevant_source: MinimalSource,
    ) -> bool:

        if retrieved_source.file_path != relevant_source.file_path:
            return False

        return (
            retrieved_source.first_character_index
            < relevant_source.last_character_index
            and relevant_source.first_character_index
            < retrieved_source.last_character_index
        )

    def __evaluate_student_question_search_against_ground_truth(
        self,
        student_question: MinimalSearchResults,
        truth_question: AnsweredQuestionGroundTruth,
    ) -> RecallStats:

        relevant_sources: list[MinimalSource] = list(
            {
                (
                    source.file_path,
                    source.first_character_index,
                    source.last_character_index,
                ): source
                for source in truth_question.sources
            }.values()
        )

        if not relevant_sources:
            raise RecallError(
                f"No relevant sources found for question "
                f"{truth_question.question_id}."
            )

        retrieved_sources: list[MinimalSource] = (
            student_question.retrieved_sources
        )

        def calculate_recall_at_k(k: int) -> float:

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
        self, dataset_path: str
    ) -> GroundTruthModel:

        try:
            with open(dataset_path, "r") as file:
                return GroundTruthModel.model_validate_json(file.read())

        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])

        except Exception as error:
            raise RecallError(str(error))

    def __load_and_validate_student_search_results(
        self, student_search_results_path: str
    ) -> StudentSearchResults:

        try:
            with open(student_search_results_path, "r") as file:
                return StudentSearchResults.model_validate_json(
                    file.read()
                )

        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])

        except Exception as error:
            raise RecallError(str(error))


recallk: RecallK = RecallK()

__all__ = ["recallk", "RecallError", "RecallStats"]
