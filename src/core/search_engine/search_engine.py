from typing import cast
import re
from .types import SearchMethod, SearchType
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS
from src.core.entities import  Question, Document, QuestionDocument
from .invert_index import InvertIndex
from src.core.validation_models import (
    MinimalSearchResults,
    MinimalSource,
)
from src.server.repositories import QuestionRepositoryInterface


class SearchEngine:
    def __init__(
        self,
         /, 
         *,
         invert_index: InvertIndex,
         question_repository: QuestionRepositoryInterface,
    ) -> None:
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)
        self.__invert_index: InvertIndex = invert_index
        self.__semantic_search: SearchMethod | None = None
        self.__lexical_search: SearchMethod | None = None
        self.__question_repository: QuestionRepositoryInterface = question_repository

    def __call__(
        self,
        *,
        question: str,
        top_k: int,
        search_type: SearchType
    ) -> MinimalSearchResults:
        # get query Terms
        cache_question: Question | None = self.__question_repository.get(question)
        minimal_search_results: MinimalSearchResults
        if cache_question is None or cache_question.top_k != top_k or cache_question.search_type != search_type.name:
            if cache_question:
                self.__question_repository.delete(question)
            new_question: Question = Question(
                question=question,
                top_k=top_k,
                search_type=search_type.name
            )
            self.__question_repository.create(new_question)
            minimal_search_results = self.__run_search_and_store_in_cache(new_question, top_k)
        else:
            minimal_search_results = self.__get_documents_from_cache(cache_question)
        return minimal_search_results


    def __tokenize(self, query: str) -> list[str]:
        query_terms: list[str] = [
            word
            for word in cast(
                list[str], self.__regex_pattern.findall(query.lower())
            )
            if word not in STOP_WORDS
        ]
        return query_terms

    def __run_search_and_store_in_cache(self, question: Question, top_k: int) -> MinimalSearchResults:
        query_terms: list[str] = self.__tokenize(question.question)
        self.__invert_index(query_terms)
        lexical_documents: list[Document] = self.__get_lexical_search(question.question, top_k)
        high_score_documents: list[Document]
        if question.search_type == "LEXICAL":
            high_score_documents = lexical_documents
        else: # search_type =  hybrid
            top_semantic_search = int(.3 * top_k)
            top_lexical_search = top_k - top_semantic_search
            lexical_documents = lexical_documents[:top_lexical_search]
            semantic_documents: list[Document] = self.__get_semantic_search(
                question.question,
                top_k
            )[:top_semantic_search]
            high_score_documents = lexical_documents + semantic_documents
        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
                file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index
            ) for doc in high_score_documents
        ]
        question_documents_to_create = [
            QuestionDocument(
                question=question,
                document=document
             ) for document in high_score_documents
        ]
        self.__question_repository.create_many_question_document(question_documents_to_create)
        return MinimalSearchResults(
            question_id= question.id,
            question = question.question,
            retrieved_sources=retrieved_sources
        )

    @property
    def __get_semantic_search(self) -> SearchMethod:
        if self.__semantic_search is None:
            from .semantic_search import semantic_search
            self.__semantic_search = semantic_search
        return self.__semantic_search

    @property
    def __get_lexical_search(self) -> SearchMethod:
        if self.__lexical_search is None:
            from .lexical_search import lexical_search
            self.__lexical_search = lexical_search
        return self.__lexical_search

    def __get_documents_from_cache(self, question: Question) -> MinimalSearchResults:
        documents: list[Document] =  self.__question_repository.get_question_documents(question.question)
        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
                file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index
            ) for doc in documents
        ]
        minimal_search_results: MinimalSearchResults = MinimalSearchResults(
            question_id=question.id,
            question=question.question,
            retrieved_sources=retrieved_sources
        )
        return minimal_search_results
