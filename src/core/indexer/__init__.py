from src.server.repositories import (
    document_repository,
    document_term_repository,
    file_repository,
)

from .indexer import Indexer

indexer: Indexer = Indexer(
    document_term_repository=document_term_repository,
    document_repository=document_repository,
    file_repository=file_repository,
)

__all__ = ["indexer", "Indexer"]
