from src.server.repositories import question_repository
from .search_engine import SearchEngine, SearchEngineError
from .types import SearchType
from .invert_index import invert_index

search_engine: SearchEngine = SearchEngine(
    invert_index=invert_index, question_repository=question_repository
)

__all__ = [
    "search_engine",
    "SearchEngine",
    "SearchType",
    "SearchEngineError",
]
