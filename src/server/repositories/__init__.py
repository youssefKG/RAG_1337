from .file_repository import FileRepository
from .document_repository import DocumentRepository
from .term_repository import TermRepository
from .question_repository import QuestionRepository
from .repositories import (
    FileRepositoryInterface,
    DocumentRepositoryInterface,
    TermRepositoryInterface,
    QuestionRepositoryInterface
)

from .errors import DBError, DBNotFoundError, DBDuplicateValueError


file_repository: FileRepository = FileRepository()
document_repository = DocumentRepository(file_repository)
term_repository: TermRepository = TermRepository(
    document_repository=document_repository
)
question_repository: QuestionRepository = QuestionRepository()

__all__ = [
    # file repository
    "file_repository",
    "FileRepository",
    "FileRepositoryInterface",
    # document repository
    "document_repository",
    "DocumentRepository",
    "DocumentRepositoryInterface",
    # document term repository
    "term_repository",
    "TermRepository",
    "TermRepositoryInterface",
    # database errors:
    "DBError",
    "DBDuplicateValueError",
    "DBNotFoundError",
    # question
    "QuestionRepositoryInterface",
    "question_repository"
]
