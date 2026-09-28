from src.server.repositories import (
    document_repository,
    term_repository,
    file_repository,
)

from .indexer import Indexer
from src.vector_db import vector_document_repository

indexer: Indexer = Indexer(
    term_repository=term_repository,
    document_repository=document_repository,
    file_repository=file_repository,
    vector_document_repository=vector_document_repository
)

__all__ = ["indexer", "Indexer"]
