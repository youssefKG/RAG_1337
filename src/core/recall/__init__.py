from pydantic import ValidationError
from typing import Annotated, TypeAlias
from src.core.validation_models import (
    RagDataset,
    StudentSearchResults,
    MinimalSource,
    AnsweredQuestion,
    UnansweredQuestion
)

class GroundTruthModel(RagDataset):
    difficulty: str
    is_valid: bool



class RecallError(Exception):
    ...

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
        total_num_of_questions_width_sources: int = len(ground_truth.rag_questions)
        total_num_of_questions_with_student_sources: int = ( 
            self.__count_total_number_of_questions_with_sources(
                ground_truth.rag_questions
            )
        )

    def __load_and_validate_dataset_path(self, dataset_path: str) -> GroundTruthModel:
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


    def __count_total_number_of_questions_with_sources(self, rag_questions: list[AnsweredQuestion| UnansweredQuestion]) -> int:
        return sum(
            1 for question in rag_questions 
            if  isinstance(question, AnsweredQuestion)
            and len(question.sources)
        )


    def __load_and_validate_student_search_results(self, student_search_results_path: str) -> StudentSearchResults:
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

    def __recall(
        self,
        student_sources: list[MinimalSource],
        ground_truth_sources: list[MinimalSource]
    ) -> _RecallK:
        pass
