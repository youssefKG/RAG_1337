from src.server.repositories import (
    document_repository,
    term_repository,
    question_repository
)
from .BM25 import BM25
from .invert_index import InvertIndex
from .search_engine import SearchEngine
from .types import SearchType
from .semantic_search import SemanticSearch
from src.vector_db import vector_document_repository



invert_index: InvertIndex = InvertIndex(
    term_repository=term_repository,
)

lexical_search: BM25 = BM25(
    avg_documents_length=document_repository.get_avg_document_length,
    total_number_of_documents=document_repository.count,
    invert_index=invert_index.invert_index,
)

semantic_search: SemanticSearch =  SemanticSearch(
    vector_document_repository=vector_document_repository
)

search_engine = SearchEngine(
    lexical_search=lexical_search,
    semantic_search=semantic_search,
    invert_index=invert_index,
    question_repository=question_repository
)

__all__ = ["search_engine", "SearchEngine", "SearchType"]
