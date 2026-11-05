"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from django.http import HttpResponse, HttpRequest
from src.core.indexer import indexer, IndexerError
from django.views.decorators.csrf import csrf_exempt
from pydantic import BaseModel, ValidationError, Field
from src.core.validation_models import MinimalSearchResults
from src.core.question_manager import question_manager, QuestionManagerError
from src.core.answer_manager import answer_manager, AnswerError
import json

CORPUS_PATH = "data/raw/vllm-0.10.1"

class CustomError(Exception):
    ...


def get_pydantic_errors_json(errors: ValidationError) -> str:
    validation_errors: list[dict[str, str]] = [
        {"field": str(err["loc"][0]), "message": err["msg"]}
        for err in errors.errors()
    ]
    validation_errors_json: str = json.dumps(validation_errors, indent=4)
    return validation_errors_json


class IndexerParams(BaseModel):
    max_chunk_size: int = Field(default=2000, le=2000, gt=400)
    is_hybrid: bool = False


class IndexerResponse(BaseModel):
    message: str


class SearchParams(BaseModel):
    query: str = Field(min_length=3)
    k: int = Field(default=5, le=10, gt=0)
    is_hybrid: bool = False


class AnswerParams(BaseModel):
    k: int = Field(default=5, gt=0, le=10)
    query: str = Field(min_length=3)
    is_hybrid: bool = False


class AnswerResponse(BaseModel):
    query: str
    answer: str | None = None
    error_message: str | None = None


class RagApi:
    @staticmethod
    @csrf_exempt
    def index(request: HttpRequest):
        if request.method != "POST":
            return HttpResponse(
                "Method not allowed. Only POST requests are supported.",
                status=400,
            )
        try:
            indexer_params: IndexerParams = IndexerParams.model_validate_json(
                request.body
            )
            indexer(
                corpus_path=CORPUS_PATH,
                max_chunk_size=indexer_params.max_chunk_size,
                is_hybrid=indexer_params.is_hybrid,
            )
            response: IndexerResponse = IndexerResponse(
                message="The Corpus {CORPUS_PATH} is successflly indexed."
            )
            return HttpResponse(response.model_dump_json(indent=4))
        except ValidationError as error:
            validation_errors_json: str = get_pydantic_errors_json(error)
            return HttpResponse(validation_errors_json, status=400)
        except IndexerError as error:
            return HttpResponse(str(error), status=400)
        except Exception as error:
            return HttpResponse(str(error), status=400)

    @staticmethod
    @csrf_exempt
    def search(request: HttpRequest) -> HttpResponse:
        if request.method != "POST":
            return HttpResponse(
                "Method not allowed. Only POST request are supported"
            )
        try:
            search_params: SearchParams = SearchParams.model_validate_json(
                request.body
            )
            try:
                minimal_search_results: MinimalSearchResults = (
                    question_manager.search(
                        search_params.query,
                        search_params.k,
                        search_params.is_hybrid,
                    )
                )
                minimal_search_results_json: str = (
                    minimal_search_results.model_dump_json(indent=4)
                )
                return HttpResponse(minimal_search_results_json, status=200)
            except QuestionManagerError as error:
                return HttpResponse(str(error), status=400)
        except ValidationError as errors:
            validation_errors_json: str = get_pydantic_errors_json(errors)
            return HttpResponse(validation_errors_json, status=400)
        except Exception as error:
            return HttpResponse(str(error), status=400)

    @staticmethod
    @csrf_exempt
    def answer(request: HttpRequest) -> HttpResponse:
        if request.method != "POST":
            return HttpResponse(
                "Method not allowed. Only POST request are supported"
            )
        try:
            answer_params: AnswerParams = AnswerParams.model_validate_json(
                request.body
            )
            try:
                answer: str = answer_manager.answer(
                    answer_params.query,
                    answer_params.k,
                    answer_params.is_hybrid,
                )
                answer_response_json = AnswerResponse(
                    query=answer_params.query, answer=answer
                ).model_dump_json(indent=4)
                return HttpResponse(answer_response_json, status=200)
            except AnswerError as error:
                answer_response_json = AnswerResponse(
                    error_message=str(error), query=answer_params.query
                ).model_dump_json(indent=4)
                return HttpResponse(answer_response_json)
        except ValidationError as error:
            validation_errors_json: str = get_pydantic_errors_json(error)
            return HttpResponse(validation_errors_json, status=400)
        except Exception as error:
            return HttpResponse(str(error), status=400)


urlpatterns = [
    path("index", RagApi.index, name="index"),
    path("search", RagApi.search, name="search"),
    path("answer", RagApi.answer, name="answer"),
]
