from .indexer import Indexer
from src.server.repositories import (
    document_repository,
    term_repository,
    file_repository,
    question_repository
)
from src.vector_db import vector_document_repository
from src.core.config_manager import config_manager

indexer: Indexer = Indexer(
    term_repository=term_repository,
    document_repository=document_repository,
    file_repository=file_repository,
    config_manager=config_manager,
    vector_document_repository=vector_document_repository,
    question_repository=question_repository
)

__all__ = ["indexer", "Indexer"]
