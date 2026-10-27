from pydantic import ValidationError
from dataclasses import dataclass
from typing import Annotated, TypeAlias
from src.core.validation_models import (
    RagDataset,
    StudentSearchResults,
    MinimalSource,
    AnsweredQuestion,
    MinimalSearchResults
)

class GroundTruthModel(RagDataset):
    difficulty: str
    is_valid: bool



class RecallError(Exception):
    ...

@dataclass(frozen=False)
class RecallStats:
    recall_1: float = 0.
    recall_3: float = 0.
    recall_5: float = 0.
    recall_10: float = 0.

_RecallK: TypeAlias = tuple[
    Annotated[int, "recall@1"],
    Annotated[int, "recall@3"],
    Annotated[int, "recall@5"],
    Annotated[int, "recall@10"]
]

class Recall:
    def __init__(self) -> None:
        pass

    def evaluate(
        self,
        student_search_results_path: str,
        dataset_path: str
     ) -> None:
        ground_truth: GroundTruthModel = self.__load_and_validate_dataset_path(dataset_path)
        student_search_results: StudentSearchResults = (
            self.__load_and_validate_student_search_results(student_search_results_path)
        )
        total_num_of_questions: int = len(ground_truth.rag_questions)
        total_num_of_questions_width_sources: int = (
            sum(
                1 
                for question in ground_truth.rag_questions 
                if isinstance(question, AnsweredQuestion)
                and len(question.sources)
            )
        )
        total_num_of_questions_with_student_sources: int = (
            sum(
                1 
                for minimal_search_results in student_search_results.search_results 
                if len(minimal_search_results.retrieved_sources)
            )
        )

    def __load_and_validate_dataset_path(
        self,
        dataset_path: str
    ) -> GroundTruthModel:
        ground_truth: GroundTruthModel
        try:
            with open(dataset_path, "r") as file:
                file_content: str = file.read()
                ground_truth = GroundTruthModel.model_validate_json(file_content)
        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])
        except Exception as error:
            raise RecallError(str(error))
        return ground_truth


    def __get_recall_stats(
        self,
        ground_truth: GroundTruthModel,
        student_search_results: StudentSearchResults
    ) -> RecallStats:
        recall_stats: RecallStats = RecallStats()
        for student_question, ground_truth_question in zip(student_search_results.search_results, ground_truth.rag_questions):
            if not isinstance(ground_truth_question, AnsweredQuestion):
                # TODO: add proper error message
                raise RecallError("")
            for idx, (student_question, ground_truth_question) in enumerate(zip(student_question.retrieved_sources, ground_truth_question.sources)):
                pass
        return recall_stats


    def __relevent_results(self, student_question: MinimalSearchResults, truth_question: AnsweredQuestion) -> int:
        if (
            student_question.question_id != truth_question.question_id
            or student_question.question != truth_question
        ):
            raise RecallError(
                "The student question does not match the truth question. "
                + f"Student question ID: {student_question.question_id}, "
                + f"Truth question ID: {truth_question.question_id}. "
                + f"Student question: {student_question.question!r}, "
                + f"Truth question: {truth_question.question!r}."
            )

    def __load_and_validate_student_search_results(
        self,
        student_search_results_path: str
    ) -> StudentSearchResults:
        student_search_results: StudentSearchResults
        try:
            with open(student_search_results_path, "r") as file:
                file_content: str = file.read()
                student_search_results = StudentSearchResults.model_validate_json(file_content)
        except ValidationError as error:
            raise RecallError(error.errors()[0]["msg"])
        except Exception as error:
            raise RecallError(str(error))
        return student_search_results

