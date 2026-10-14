from typing import cast
import re
from .types import SearchMethod, SearchType
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS
from src.core.entities import  Question, QuestionDocument, Document
from .invert_index import InvertIndex
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    MinimalSource,
)
from src.server.repositories import QuestionRepositoryInterface, DocumentRepositoryInterface


class SearchEngine:
    def __init__(
        self,
         /, 
         *,
         semantic_search: SearchMethod,
         lexical_search: SearchMethod,
         invert_index: InvertIndex,
         question_repository: QuestionRepositoryInterface,
         document_repository: DocumentRepositoryInterface
    ) -> None:
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)
        self.__invert_index: InvertIndex = invert_index
        self.__semantic_search: SearchMethod = semantic_search
        self.__lexical_search: SearchMethod = lexical_search
        self.__question_repository: QuestionRepositoryInterface = question_repository
        self.__document_repository: DocumentRepositoryInterface = document_repository

    def __call__(
            self, *, question: UnansweredQuestion, top_k: int, search_type: SearchType
    ) -> MinimalSearchResults:
        # get query Terms
        cache_question: Question | None = self.__question_repository.get(question.question)
        if cache_question is None or cache_question.top_k != top_k:
            if cache_question:
                self.__question_repository.delete(question.question)
            new_question: Question = Question(question=question.question, top_k=top_k)
            self.__question_repository.create(new_question)
        else:
            question_documents: list[Document] = self.__document_repository.get_question_documents(question.question)
        query_terms: list[str] = [
            word
            for word in cast(
                list[str], self.__regex_pattern.findall(question.question.lower())
            )
            if word not in STOP_WORDS
        ]
        # update the invert index with new terms
        self.__invert_index(query_terms)
        # run bm25 and get top k high score documents
        condidate_documents: list[Document] = self.__lexical_search(query_terms, top_k)
        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
                file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index
                ) for doc in condidate_documents
        ]
        minimal_search_result: MinimalSearchResults = MinimalSearchResults(
            question_id=question.question_id,
            question=question.question,
            retrieved_sources=retrieved_sources,
        )
        return minimal_search_result
    
