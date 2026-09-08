from .file_repository import FileRepository
from .document_repository import DocumentRepository
from .document_term_repository import DocumentTermRepository
from .repositories import (
    FileRepositoryInterface,
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)
from .errors import DBError, DBNotFoundError, DBDuplicateValueError


file_repository: FileRepository = FileRepository()
document_repository = DocumentRepository(file_repository)
document_term_repository: DocumentTermRepository = DocumentTermRepository(
    document_repository=document_repository
)

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
    "document_term_repository",
    "DocumentTermRepository",
    "DocumentTermRepositoryInterface",
    # database errors:
    "DBError",
    "DBDuplicateValueError",
    "DBNotFoundError",
]
