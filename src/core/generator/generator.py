from core.search_engine import SearchEngine
from src.core.indexer import indexer


class Generator:
    def __init__(self, search_engine: SearchEngine, indexer: Indexer) -> None:
        self.__search_engine: SearchEngine = search_engine
