from typing import cast
import re
from .types import SearchMethod, SearchType
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS
from src.core.entities import  Question, Document, QuestionDocument
from .invert_index import InvertIndex
from src.core.validation_models import (
    MinimalSearchResults,
    UnansweredQuestion,
    MinimalSource,
)
from src.server.repositories import QuestionRepositoryInterface


class SearchEngine:
    def __init__(
        self,
         /, 
         *,
         semantic_search: SearchMethod,
         lexical_search: SearchMethod,
         invert_index: InvertIndex,
         question_repository: QuestionRepositoryInterface,
    ) -> None:
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)
        self.__invert_index: InvertIndex = invert_index
        self.__semantic_search: SearchMethod = semantic_search
        self.__lexical_search: SearchMethod = lexical_search
        self.__question_repository: QuestionRepositoryInterface = question_repository

    def __call__(
        self,
        *,
        question: UnansweredQuestion,
        top_k: int,
        search_type: SearchType
    ) -> MinimalSearchResults:
        # get query Terms
        cache_question: Question | None = self.__question_repository.get(question.question)
        minimal_search_results: MinimalSearchResults
        if cache_question is None or cache_question.top_k < top_k or cache_question.search_type != search_type.name:
            if cache_question:
                self.__question_repository.delete(question.question)
            new_question: Question = Question(
                id=question.question_id,
                question=question.question,
                top_k=top_k,
                search_type=search_type.name
            )
            self.__question_repository.create(new_question)
            minimal_search_results = self.__run_search(new_question, top_k)
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

    # def __get_minimal_search_results(
    #     self,
    #     question: UnansweredQuestion,
    #     top_k: int,
    #     search_type: SearchType
    # ) -> MinimalSearchResults:
    #     query_terms: list[str] = self.__tokenize(question.question)
    #     self.__invert_index(query_terms)
    #     semantic_documents: list[Document] = self.__semantic_search(query_terms, top_k)
    #     lexical_documents: list[Document] = self.__lexical_search(query_terms, top_k)
    #     semantic_doc_len: int
    #     lexical_doc_len: int
    #     match search_type:
    #         case SearchType.LEXICAL:
    #             lexical_doc_len = top_k
    #             semantic_doc_len = 0;
    #         case SearchType.HYBRID:
    #             semantic_doc_len = int(.2 * top_k)
    #             lexical_doc_len = top_k - semantic_doc_len
    #     if semantic_doc_len > len(semantic_documents):
    #         semantic_doc_len = len(semantic_documents)
    #     if lexical_doc_len > len(lexical_documents):
    #         lexical_doc_len = len(lexical_documents)
    #     lexical_docs: list[Document] = lexical_documents[:lexical_doc_len]
    #     semantic_docs: list[Document] = semantic_documents[:semantic_doc_len]
    #     chosen_documents: list[Document] = lexical_docs + semantic_docs
    #     retrieved_sources: list[MinimalSource] = [
    #         MinimalSource(
    #             file_path=doc.file.path,
    #             first_character_index=doc.start_index,
    #             last_character_index=doc.end_index
    #         ) for doc in chosen_documents
    #     ]
    #     minimal_search_results: MinimalSearchResults = MinimalSearchResults(
    #         question_id=question.question_id,
    #         question=question.question,
    #         retrieved_sources=retrieved_sources
    #     )
    #     return minimal_search_results

    def __run_search(self, question: Question, top_k: int) -> MinimalSearchResults:
        query_terms: list[str] = self.__tokenize(question.question)
        minimal_search_results: MinimalSearchResults
        lexical_documents: list[Document]
        semantic_documents: list[Document]
        self.__invert_index(query_terms)
        if question.search_type == "LEXICAL":
            lexical_documents = self.__lexical_search(query_terms, top_k)
            retrieved_sources = [
                MinimalSource(file_path=doc.file.path,
                    first_character_index=doc.start_index,
                    last_character_index=doc.end_index
                ) for doc in lexical_documents
            ]
            minimal_search_results = MinimalSearchResults(
                question_id=question.id,
                question=question.question,
                retrieved_sources=retrieved_sources
            )
        else:
            top_semantic_search = int(0.2 * top_k)
            top_lexical_search = top_k - top_semantic_search
            lexical_documents = self.__lexical_search(query_terms, top_k)[:top_lexical_search]
            semantic_documents= list()
            hybrid_documents: list[Document] = lexical_documents + semantic_documents
            retrieved_sources: list[MinimalSource] = [
                MinimalSource(
                    file_path=doc.file.path,
                    first_character_index=doc.start_index,
                    last_character_index=doc.end_index
                ) for doc in hybrid_documents
            ]
            minimal_search_results = MinimalSearchResults(
                question_id= question.id,
                question = question.question,
                retrieved_sources=retrieved_sources
            )
        return minimal_search_results



    def __get_documents_from_cache(self, question: Question) -> MinimalSearchResults:
        documents: list[Document] =  self.__question_repository.get_question_documents(question.question)
        retrieved_sources: list[MinimalSource] = [MinimalSource(
            file_path=doc.file.path,
            first_character_index=doc.start_index,
            last_character_index=doc.end_index
        ) for doc in documents]
        minimal_search_results: MinimalSearchResults = MinimalSearchResults(
            question_id=question.id,
            question=question.question,
            retrieved_sources=retrieved_sources
        )
        return minimal_search_results
