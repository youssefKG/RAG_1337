from typing import cast
import re
from .types import SearchMethod
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS
from src.server.entities import DocumentInterface
from .invert_index import InvertIndex
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    MinimalSource,
)


class SearchEngine:
    def __init__(self, /, *, bm25: SearchMethod, invert_index: InvertIndex) -> None:
        self.__bm25: SearchMethod = bm25
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)
        self.__invert_index: InvertIndex = invert_index

    def __call__(
        self, question: UnansweredQuestion, top_k: int
    ) -> MinimalSearchResults:
        query_terms: list[str] = [
            word
            for word in cast(
                list[str], self.__regex_pattern.findall(question.question.lower())
            )
            if word not in STOP_WORDS
        ]
        self.__invert_index(query_terms)
        condidate_documents: list[DocumentInterface] = self.__bm25(query_terms, top_k)
        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
               file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index,
            )
            for doc in condidate_documents
        ]
        minimal_search_result: MinimalSearchResults = MinimalSearchResults(
            question_id=question.question_id,
            question=question.question,
            retrieved_sources=retrieved_sources,
        )
        return minimal_search_result
