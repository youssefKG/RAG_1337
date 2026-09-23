from src.server.repositories import (
    document_repository,
    document_term_repository,
)
from .BM25 import BM25
from .invert_index import InvertIndex
from .search_engine import SearchEngine

invert_index: InvertIndex = InvertIndex(
    document_term_repository=document_term_repository,
)

bm25: BM25 = BM25(
    avg_documents_length=document_repository.get_avg_document_length,
    total_number_of_documents=document_repository.count,
    invert_index=invert_index.invert_index,
)

search_engine = SearchEngine(bm25=bm25, invert_index=invert_index)

__all__ = ["search_engine"]
