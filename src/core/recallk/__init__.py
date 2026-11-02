from typing import override
from pydantic import ValidationError, BaseModel
from dataclasses import dataclass
from src.core.validation_models import (
    StudentSearchResults,
    AnsweredQuestion,
    MinimalSearchResults,
)


class AnsweredQuestionGroundTruth(AnsweredQuestion):
    difficulty: str
    is_valid: bool


class GroundTruthModel(BaseModel):
    rag_questions: list[AnsweredQuestionGroundTruth]


class RecallError(Exception):
    ...


@dataclass(frozen=False)
class RecallStats:
    recall_3: float
    recall_5: float
    recall_10: float
    recall_1: float

    @override
    def __str__(self) -> str:
        return (
            f"\nRecall@1:  {self.recall_1:.4f} ({self.recall_1 * 100:.1f}%)\n"
            f"Recall@3:  {self.recall_3:.4f} ({self.recall_3 * 100:.1f}%)\n"
            f"Recall@3:  {self.recall_5:.4f} ({self.recall_5 * 100:.1f}%)\n"
            f"Recall@3:  {self.recall_10:.4f} ({self.recall_10 * 100:.1f}%)"
        )


class RecallK:

    def __call__(
        self, student_search_results_path: str, dataset_path: str
    ) -> RecallStats:
        ground_truth: GroundTruthModel = self.__load_and_validate_dataset_path(
            dataset_path
        )
        student_search_results: StudentSearchResults = (
            self.__load_and_validate_student_search_results(
                student_search_results_path
            )
        )
        total_num_of_questions: int = len(ground_truth.rag_questions)
        student_questions: list[MinimalSearchResults] = (
            student_search_results.search_results
        )
        ground_truth_questions: list[AnsweredQuestionGroundTruth] = (
            ground_truth.rag_questions
        )
        if len(student_questions) != len(ground_truth_questions):
            raise RecallError(
                "The number of student questions does not match the "
                + "number of ground-truth questions. "
                + f"Student questions: {len(student_questions)}, "
                + f"ground-truth questions: {len(ground_truth_questions)}."
            )

        recall_stats: RecallStats = RecallStats(
            recall_1=0.0, recall_3=0.0, recall_5=0.0, recall_10=0.0
        )
        for student_question, ground_truth_question in zip(
            student_search_results.search_results, ground_truth.rag_questions
        ):
            question_recall_stats: RecallStats = (
                self.__evaluate_student_question_search_against_ground_truth(
                    student_question, ground_truth_question
                )
            )
            recall_stats.recall_1 += question_recall_stats.recall_1
            recall_stats.recall_3 += question_recall_stats.recall_3
            recall_stats.recall_5 += question_recall_stats.recall_5
            recall_stats.recall_10 += question_recall_stats.recall_10
        recall_stats.recall_1 /= total_num_of_questions
        recall_stats.recall_3 /= total_num_of_questions
        recall_stats.recall_5 /= total_num_of_questions
        recall_stats.recall_10 /= total_num_of_questions
        return recall_stats

    def __load_and_validate_dataset_path(
        self, dataset_path: str
    ) -> GroundTruthModel:
        ground_truth: GroundTruthModel
        try:
            with open(dataset_path, "r") as file:
                file_content: str = file.read()
                ground_truth = GroundTruthModel.model_validate_json(
                    file_content
                )
        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])
        except Exception as error:
            raise RecallError(str(error))
        return ground_truth

    def __evaluate_student_question_search_against_ground_truth(
        self,
        student_question: MinimalSearchResults,
        truth_question: AnsweredQuestion,
    ) -> RecallStats:
        recall_stats: RecallStats = RecallStats(
            recall_1=0.0, recall_3=0.0, recall_5=0.0, recall_10=0.0
        )
        if (
            student_question.question_id != truth_question.question_id
            or student_question.question != truth_question.question
        ):
            raise RecallError(
                "The student question does not match the truth question. "
                + f"Student question ID: {student_question.question_id}, "
                + f"Truth question ID: {truth_question.question_id}. "
                + f"Student question: {student_question.question!r}, "
                + f"Truth question: {truth_question.question!r}."
            )
        for idx, retrieved_source in enumerate(
            student_question.retrieved_sources
        ):
            if any(
                retrieved_source
                for ground_truth_source in truth_question.sources
                if retrieved_source.file_path == ground_truth_source.file_path
            ):
                match idx + 1:
                    case 1:
                        recall_stats.recall_1 += 1.0
                    case 3:
                        recall_stats.recall_3 += 1.0
                    case 5:
                        recall_stats.recall_5 += 1.0
                    case 10:
                        recall_stats.recall_10 += 1.0
                    case _:
                        break
        recall_stats.recall_3 += recall_stats.recall_1
        recall_stats.recall_5 += recall_stats.recall_3
        recall_stats.recall_10 += recall_stats.recall_5
        return recall_stats

    def __load_and_validate_student_search_results(
        self, student_search_results_path: str
    ) -> StudentSearchResults:
        student_search_results: StudentSearchResults
        try:
            with open(student_search_results_path, "r") as file:
                file_content: str = file.read()
                student_search_results = (
                    StudentSearchResults.model_validate_json(file_content)
                )
        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])
        except Exception as error:
            raise RecallError(str(error))
        return student_search_results


recallk: RecallK = RecallK()

__all__ = ["recallk", "RecallError", "RecallStats"]
