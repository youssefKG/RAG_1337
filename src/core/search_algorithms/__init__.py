from src.server.repositories import (
    document_repository,
    document_term_repository,
)
from .BM25_index import BM25Index
from .invert_index import InvertIndex

invert_index: InvertIndex = InvertIndex(
    document_repository=document_repository,
    document_term_repository=document_term_repository,
)

bm25: BM25Index = BM25Index(
    avg_documents_length=invert_index.avg_document_length,
    total_number_of_documents=invert_index.total_number_of_documents,
    invert_index=invert_index.invert_index,
)

__all__ = ["invert_index", "bm25"]
