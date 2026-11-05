"""Implement BM25-based lexical document retrieval.

This module provides a BM25 ranking algorithm for retrieving relevant
documents from an inverted index based on query term frequency and
inverse document frequency.

It calculates document relevance scores using term frequency,
inverse document frequency, and document length normalization,
then returns the highest-ranked documents.
"""

import re
from dataclasses import dataclass
from typing import Annotated, TypeAlias, cast
import math

from src.core.entities import Document
from .invert_index import InvertIndexType, PostingType, invert_index
from src.server.repositories import document_repository
from src.core.utils import TOKENIZER_REGEX_PATTERN, STOP_WORDS

_TermIDFS: TypeAlias = dict[
    Annotated[str, "term value"], Annotated[float, "idf(t) score"]
]


@dataclass(frozen=False)
class DocumentScore:
    """Represent a document and its calculated relevance score."""

    document: Document
    score: float = 0


_DocumentScoreType: TypeAlias = dict[
    Annotated[str, "document id"], DocumentScore
]


class BM25:
    """Rank documents using the BM25 lexical retrieval algorithm."""

    def __init__(
        self,
        *,
        k: float = 1.2,
        b: float = 0.75,
        avg_documents_length: float,
        total_number_of_documents: int,
        invert_index: InvertIndexType,
    ) -> None:
        """Initialize the BM25 ranking algorithm.

        Args:
            k: Controls term frequency saturation.
            b: Controls document length normalization.
            avg_documents_length: Average length of documents in the corpus.
            total_number_of_documents: Total number of documents in the corpus.
            invert_index: Inverted index containing term postings.
        """
        self.__k: float = k
        self.__b: float = b
        self.__avg_document_length: float = avg_documents_length
        self.__total_number_of_documents: int = total_number_of_documents
        self.__invert_index: InvertIndexType = invert_index
        self.__idfs_score: _TermIDFS = _TermIDFS()
        self.__regex_pattern = re.compile(TOKENIZER_REGEX_PATTERN)

    def __call__(
        self,
        question: str,
        top_k: int,
    ) -> list[Document]:
        """Retrieve the highest-ranked documents for a search query.

        Tokenizes the query, calculates BM25 relevance scores for documents
        containing its terms, and returns the top-ranked documents.

        Args:
            question: Search query used to retrieve relevant documents.
            top_k: Maximum number of documents to return.

        Returns:
            Documents ordered by descending BM25 relevance score.
        """
        query_terms: list[str] = self.__tokenize(question)
        chosen_documents: _DocumentScoreType = _DocumentScoreType()
        for term in query_terms:
            if term in self.__invert_index:
                posting: PostingType = self.__invert_index[term]
                for document_id, (
                    document,
                    term_frequency,
                ) in posting.items():
                    if document_id not in chosen_documents:
                        chosen_documents[document_id] = DocumentScore(
                            document=document, score=0
                        )
                    chosen_documents[
                        document_id
                    ].score += self.__score_document(
                        document, term, term_frequency, len(posting)
                    )
        high_score_document: list[DocumentScore] = sorted(
            chosen_documents.values(),
            key=lambda x: x.score,
            reverse=True,
        )[:top_k]
        return [doc.document for doc in high_score_document]

    def __score_document(
        self,
        document: Document,
        term: str,
        term_frequency: int,
        number_of_document_contain_term: int,
    ) -> float:
        """Calculate the BM25 contribution of a query term to a document.

        Args:
            document: Document being evaluated.
            term: Query term used to calculate relevance.
            term_frequency: Number of occurrences of the term in the document.
            number_of_document_contain_term: Number of documents containing
                the query term.

        Returns:
            BM25 score contribution of the query term.
        """
        idf_score: float = self.__get_idf_score(
            term, number_of_document_contain_term
        )
        tf_score: float = self.__tf(document.length, term_frequency)
        return tf_score * idf_score

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        """Calculate the normalized term frequency component of BM25.

        Args:
            doc_len: Length of the document.
            term_frequency: Number of occurrences of the term in the document.

        Returns:
            Normalized term frequency score.
        """
        nominator: float = term_frequency * (self.__k + 1)
        dominator: float = term_frequency + (
            self.__k
            * (
                1
                - self.__b
                + (self.__b * (doc_len / self.__avg_document_length))
            )
        )
        return float(nominator / dominator)

    def __get_idf_score(
        self, term: str, number_of_document_contain_term: int
    ) -> float:
        """Retrieve or calculate the inverse document frequency of a term.

        Previously calculated IDF scores are cached to avoid repeated
        calculations.

        Args:
            term: Term whose inverse document frequency is calculated.
            number_of_document_contain_term: Number of documents containing
                the term.

        Returns:
            Inverse document frequency score of the term.
        """
        if term not in self.__idfs_score:
            nominator: float = (
                self.__total_number_of_documents
                - number_of_document_contain_term
                + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            idf_term_score: float = math.log(nominator / dominator)
            self.__idfs_score[term] = idf_term_score
        return self.__idfs_score[term]

    def __tokenize(self, query: str) -> list[str]:
        """Tokenize a search query and remove stop words.

        Converts the query to lowercase, extracts tokens using the
        configured tokenizer pattern, and filters out stop words.

        Args:
            query: Search query to tokenize.

        Returns:
            List of normalized query terms.
        """
        query_terms: list[str] = [
            word
            for word in cast(
                list[str], self.__regex_pattern.findall(query.lower())
            )
            if word not in STOP_WORDS
        ]
        return query_terms


lexical_search: BM25 = BM25(
    avg_documents_length=document_repository.get_avg_document_length,
    total_number_of_documents=document_repository.count,
    invert_index=invert_index.invert_index,
)
