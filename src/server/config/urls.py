"""Define URL routes and API endpoints for the RAG server.

Provides HTTP endpoints for corpus indexing, document retrieval,
and answer generation.
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
    """Represent a custom exception raised by the RAG API."""


def get_pydantic_errors_json(errors: ValidationError) -> str:
    """Convert Pydantic validation errors into a JSON string.

    Args:
        errors: Validation errors raised during model validation.

    Returns:
        JSON-formatted validation errors containing field names
        and corresponding error messages.
    """
    validation_errors: list[dict[str, str]] = [
        {"field": str(err["loc"][0]), "message": err["msg"]}
        for err in errors.errors()
    ]
    validation_errors_json: str = json.dumps(validation_errors, indent=4)
    return validation_errors_json


class IndexerParams(BaseModel):
    """Define parameters accepted by the corpus indexing endpoint.

    Attributes:
        max_chunk_size: Maximum allowed size of an indexed document chunk.
        is_hybrid: Whether semantic indexing should be enabled.
    """

    max_chunk_size: int = Field(default=2000, le=2000, gt=400)
    is_hybrid: bool = False


class IndexerResponse(BaseModel):
    """Represent the response returned after corpus indexing.

    Attributes:
        message: Message describing the indexing operation.
    """

    message: str


class SearchParams(BaseModel):
    """Define parameters accepted by the document search endpoint.

    Attributes:
        query: Search query submitted by the client.
        k: Maximum number of documents to retrieve.
        is_hybrid: Whether hybrid retrieval should be used.
    """

    query: str = Field(min_length=3)
    k: int = Field(default=5, le=10, gt=0)
    is_hybrid: bool = False


class AnswerParams(BaseModel):
    """Define parameters accepted by the answer generation endpoint.

    Attributes:
        k: Maximum number of documents to retrieve.
        query: Question submitted by the client.
        is_hybrid: Whether hybrid retrieval should be used.
    """

    k: int = Field(default=5, gt=0, le=10)
    query: str = Field(min_length=3)
    is_hybrid: bool = False
    max_tokens: int = Field(default=50, gt=10, le=10)


class AnswerResponse(BaseModel):
    """Represent the response returned by the answer endpoint.

    Attributes:
        query: Original question submitted by the client.
        answer: Generated answer, if successful.
        error_message: Error description, if answer generation fails.
    """

    query: str
    answer: str | None = None
    error_message: str | None = None


class RagApi:
    """Expose HTTP endpoints for RAG operations."""

    @staticmethod
    @csrf_exempt
    def index(request: HttpRequest):
        """Index the configured corpus through an HTTP POST request.

        Validates indexing parameters, invokes the indexer, and returns
        either an indexing response or an error message.

        Args:
            request: Incoming Django HTTP request.

        Returns:
            HTTP response describing the indexing result or failure.
        """
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
        """Retrieve documents relevant to a submitted search query.

        Validates search parameters and delegates document retrieval
        to the question manager.

        Args:
            request: Incoming Django HTTP request.

        Returns:
            HTTP response containing search results or an error message.
        """
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
        """Generate an answer for a submitted question.

        Validates request parameters and delegates answer generation
        to the answer manager.

        Args:
            request: Incoming Django HTTP request.

        Returns:
            HTTP response containing the generated answer or an error.
        """
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
                    answer_params.max_tokens
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
