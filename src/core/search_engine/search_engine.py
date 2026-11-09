"""Provide lexical and semantic document retrieval capabilities.

This module implements the search engine responsible for processing
questions, retrieving relevant documents through lexical or semantic
search strategies, and caching retrieval results.

It coordinates the inverted index, search implementations, and
question repository to provide a unified document retrieval interface.
"""

import re
from .types import SearchMethod, SearchType
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS
from src.core.entities import Question, Document, QuestionDocument
from .invert_index import InvertIndex
from src.core.validation_models import (
    MinimalSearchResults,
    MinimalSource,
    UnansweredQuestion,
)
from src.server.repositories import QuestionRepositoryInterface


class SearchEngineError(Exception):
    """Raised when a search engine operation fails."""


class NoDocumentsFoundWarning(Exception):
    """Raised when a no relevent documents found."""
    pass


class SearchEngine:
    """Coordinate lexical and semantic document retrieval.

    Provides question processing, search execution, result caching,
    and conversion of retrieved documents into search result models.
    """

    def __init__(
        self,
        /,
        *,
        invert_index: InvertIndex,
        question_repository: QuestionRepositoryInterface,
    ) -> None:
        """Initialize the search engine and its dependencies.

        Args:
            invert_index: Inverted index used for lexical retrieval.
            question_repository: Repository responsible for question
                persistence and cached retrieval results.
        """
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)
        self.__invert_index: InvertIndex = invert_index
        self.__semantic_search: SearchMethod | None = None
        self.__lexical_search: SearchMethod | None = None
        self.__question_repository: QuestionRepositoryInterface = (
            question_repository
        )

    def __call__(
        self,
        *,
        unanswered_question: UnansweredQuestion,
        top_k: int,
        search_type: SearchType,
    ) -> MinimalSearchResults:
        """Retrieve relevant documents for a question.

        Checks whether a valid cached result exists before executing
        a new search. Results are cached using the question, retrieval
        strategy, and requested number of documents.

        Args:
            unanswered_question: Question to process.
            top_k: Maximum number of documents to retrieve.
            search_type: Retrieval strategy to use.

        Returns:
            Search results containing the retrieved document sources.
        """
        minimal_search_results: MinimalSearchResults
        question: str = unanswered_question.question
        cache_question: Question | None = self.__question_repository.get(
            question
        )
        if (
            cache_question is None
            or cache_question.top_k != top_k
            or cache_question.search_type != search_type.name
        ):
            if cache_question:
                self.__question_repository.delete(question)
            new_question: Question = Question(
                id=unanswered_question.question_id,
                question=question,
                top_k=top_k,
                search_type=search_type.name,
            )
            self.__question_repository.create(new_question)
            minimal_search_results = self.__run_search_and_store_in_cache(
                new_question, top_k
            )
        else:
            minimal_search_results = self.__get_documents_from_cache(
                cache_question
            )
        return minimal_search_results

    def __run_search_and_store_in_cache(
        self, question: Question, top_k: int
    ) -> MinimalSearchResults:
        """Execute retrieval and persist the resulting document associations.

        Performs tokenization and lexical retrieval, optionally combines
        semantic retrieval results, and stores the retrieved documents
        in the question repository.

        Args:
            question: Question being processed.
            top_k: Maximum number of documents to retrieve.

        Returns:
            Search results containing the retrieved document sources.
        """
        query_terms: list[str] = self.__tokenize(question.question)
        self.__invert_index(query_terms)
        lexical_documents: list[Document] = self.__get_lexical_search(
            question.question, top_k
        )
        high_score_documents: list[Document]
        if question.search_type == "LEXICAL":
            high_score_documents = lexical_documents
        else:  # search_type = hybrid
            top_semantic_search = int(0.3 * top_k)
            top_lexical_search = top_k - top_semantic_search
            lexical_documents = lexical_documents[:top_lexical_search]
            semantic_documents: list[Document] = self.__get_semantic_search(
                question.question, top_k
            )[:top_semantic_search]
            high_score_documents = lexical_documents + semantic_documents
        if not high_score_documents:
            raise NoDocumentsFoundWarning(
                "No relevant documents were found in"
                + " the knowledge base."
                + f"for question: '{question.question}"
            )

        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
                file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index,
            )
            for doc in high_score_documents
        ]
        question_documents_to_create = [
            QuestionDocument(question=question, document=document)
            for document in high_score_documents
        ]
        self.__question_repository.create_many_question_document(
            question_documents_to_create
        )
        return MinimalSearchResults(
            question_id=question.id,
            question=question.question,
            retrieved_sources=retrieved_sources,
        )

    def __tokenize(self, text: str) -> list[str]:
        """Tokenize text and expand compound identifiers.

        Removes stop words, converts tokens to lowercase, and splits
        compound identifiers written in camelCase or snake_case.

        Args:
            text: Input text to tokenize.

        Returns:
            A list of normalized tokens.
        """
        splited_text: list[str] = re.findall(TOKENIZER_REGEX_PATTERN, text)
        tokens: list[str] = []
        for token in splited_text:
            if token in STOP_WORDS:
                continue
            tokens.append(token.lower())
            expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", token)
            parts = expanded.replace("_", " ").lower().split()
            if len(parts) > 1:
                tokens.extend(parts)
        return tokens

    @property
    def __get_semantic_search(self) -> SearchMethod:
        """Lazily load and return the semantic search implementation.

        Returns:
            The semantic retrieval function.
        """
        if self.__semantic_search is None:
            from .semantic_search import semantic_search

            self.__semantic_search = semantic_search
        return self.__semantic_search

    @property
    def __get_lexical_search(self) -> SearchMethod:
        """Lazily load and return the lexical search implementation.

        Returns:
            The lexical retrieval function.
        """
        if self.__lexical_search is None:
            from .lexical_search import lexical_search

            self.__lexical_search = lexical_search
        return self.__lexical_search

    def __get_documents_from_cache(
        self, question: Question
    ) -> MinimalSearchResults:
        """Retrieve previously cached documents for a question.

        Args:
            question: Question whose associated documents are cached.

        Returns:
            Search results reconstructed from the cached documents.
        """
        documents: list[Document] = (
            self.__question_repository.get_question_documents(
                question.question
            )
        )
        retrieved_sources: list[MinimalSource] = [
            MinimalSource(
                file_path=doc.file.path,
                first_character_index=doc.start_index,
                last_character_index=doc.end_index,
            )
            for doc in documents
        ]
        minimal_search_results: MinimalSearchResults = MinimalSearchResults(
            question_id=question.id,
            question=question.question,
            retrieved_sources=retrieved_sources,
        )
        return minimal_search_results
