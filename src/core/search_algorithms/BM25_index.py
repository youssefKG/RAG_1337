from collections import defaultdict
import math


from src.server.entities import DocumentTermInterface, DocumentInterface
from src.server.repositories import (
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)
from typing import Annotated, TypeAlias

_Posting: TypeAlias = tuple[Annotated[int, "term frequency"], DocumentInterface]
_InvertIndex: TypeAlias = dict[Annotated[str, "term value"], list[_Posting]]
_TermIDFS: TypeAlias = dict[
    Annotated[str, "term value"], Annotated[float, "idf(t) score"]
]
_DocumentScore: TypeAlias = tuple[
    Annotated[int, "document id"], Annotated[float, "document score"]
]


class BM25Index:
    def __init__(
        self,
        *,
        k: float = 1,
        b: float = 0.75,
        top_k: int = 5,
        document_term_repository: DocumentTermRepositoryInterface,
        query: str,
        document_repository: DocumentRepositoryInterface,
    ) -> None:
        self.__query: str = query
        self.__k: float = k
        self.__b: float = b
        self.__top_k: int = top_k
        self.__document_term_repository: DocumentTermRepositoryInterface = (
            document_term_repository
        )
        self.__document_repository: DocumentRepositoryInterface = document_repository

        self.__avg_document_length: int = (
            self.__document_repository.get_avg_document_length
        )
        self.__total_number_of_documents: int = self.__document_repository.count
        self.__query_terms: list[str] = self.__query.split()
        self.__document_terms: list[DocumentTermInterface] = (
            self.__document_term_repository.get_by_values(self.__query_terms)
        )
        self.__document_scores: list[_DocumentScore] = list()
        self.__terms_idfs: _TermIDFS
        self.__invert_index: _InvertIndex
        self.__set_invert_index()
        self.__set_idf_terms()

    def search(
        self,
    ) -> None:
        score: float = 0.0
        passed_ids: set[int] = set()
        for doc_term in self.__document_terms:
            if doc_term.document.id in passed_ids:
                continue
            for term_value in self.__query_terms:
                document_info: (
                    None
                    | tuple[
                        Annotated[int, "document length"],
                        Annotated[int, "term frequency"],
                    ]
                ) = self.__get_document_info(doc_term.document.id, term_value)

                if document_info is None:
                    continue
                doc_len, term_frequency = document_info
                score += self.__terms_idfs[term_value] * self.__tf(
                    doc_len, term_frequency
                )
            passed_ids.add(doc_term.document.id)
            self.__document_scores.append((doc_term.document.id, score))
            score = 0.0
        self.__document_scores.sort(key=lambda element: element[1], reverse=True)
        if len(self.__document_scores) > self.__top_k:
            self.__document_scores = self.__document_scores[: self.__top_k]

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        dominator: float = term_frequency + self.__k * (
            1 - self.__b + (self.__b * (doc_len / self.__avg_document_length))
        )
        return term_frequency / dominator

    def __get_document_info(
        self, doc_id: int, term_value: str
    ) -> (
        tuple[Annotated[int, "length of document"], Annotated[int, "term frequency"]]
        | None
    ):
        documents_list: list[
            tuple[Annotated[int, "term frequency"], DocumentInterface]
        ] = self.__invert_index[term_value]
        if len(documents_list) == 0:
            return None
        for term_frequency, document in documents_list:
            if document.id == doc_id:
                return (document.length, term_frequency)
        return None

    def __set_invert_index(self) -> None:
        self.__invert_index = defaultdict(list[_Posting])
        for doc_term in self.__document_terms:
            self.__invert_index[doc_term.value].append(
                (doc_term.frequency, doc_term.document)
            )

    def get_document_term(
        self, doc_id: int, term_value: str
    ) -> DocumentTermInterface | None:
        for document_term in self.__document_terms:
            if (
                document_term.document.id == doc_id
                and document_term.value == term_value
            ):
                return document_term
        return None

    def __set_idf_terms(self) -> None:
        self.__terms_idfs = dict()
        for term in self.__query_terms:
            number_of_document_contain_term: int = len(self.__invert_index[term])
            nominator: float = (
                self.__total_number_of_documents - number_of_document_contain_term + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            self.__terms_idfs[term] = math.log(nominator / dominator)

    @property
    def documents_score(
        self,
    ) -> list[Annotated[int, "document id"]]:
        return [doc_id for doc_id, _ in self.__document_scores]
