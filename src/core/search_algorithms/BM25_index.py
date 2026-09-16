from collections import defaultdict
import math


from src.server.entities import DocumentTermInterface, DocumentInterface
from typing import Annotated, TypeAlias
from .invert_index import InvertIndexType

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
        avg_documents_length: int,
        total_number_of_documents: int,
        query: str,
        invert_index: InvertIndexType,
    ) -> None:
        self.__query: str = query
        self.__k: float = k
        self.__b: float = b
        self.__top_k: int = top_k

        self.__avg_document_length: int = avg_documents_length
        self.__total_number_of_documents: int = total_number_of_documents
        self.__query_terms: set[str] = set(self.__query.split())
        self.__document_scores: list[_DocumentScore] = list()
        self.__invert_index: InvertIndexType = invert_index

    def __call__(
        self, query: str, condidates_documents: list[DocumentInterface]
    ) -> list[DocumentTermInterface]:
        chosen_documents: list[DocumentTermInterface] = list()
        for cond_doc in condidates_documents:
            pass
        return chosen_documents

    def __score_document(
        self,
        query_terms: set[str],
        condidate_document: DocumentInterface,
        idfs_terms_score: _TermIDFS,
    ) -> float:
        score: float = 0.0
        for term in query_terms:
            idf_term: float = idfs_terms_score.get(term, 0.0)
            tf_score: float = self.__tf(condidate_document.length)
        return score

    def search(self, condidate_documents: list[DocumentTermInterface]) -> None:
        score: float = 0.0
        for doc_term in condidate_documents:
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
            self.__document_scores.append((doc_term.document.id, score))
            score = 0.0
        self.__document_scores.sort(key=lambda element: element[1], reverse=True)
        if len(self.__document_scores) > self.__top_k:
            self.__document_scores = self.__document_scores[: self.__top_k]

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        dominator: float = term_frequency + (
            self.__k
            * (1 - self.__b + (self.__b * (doc_len / self.__avg_document_length)))
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

    def get_idf_terms(self, query_terms: set[str]) -> _TermIDFS:
        idfs_terms: _TermIDFS = _TermIDFS()
        for term in query_terms:
            number_of_document_contain_term: int = len(self.__invert_index[term])
            nominator: float = (
                self.__total_number_of_documents - number_of_document_contain_term + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            idf_term_score: float = math.log(nominator / dominator)
            idfs_terms[term] = idf_term_score
        return idfs_terms

    @property
    def documents_score(
        self,
    ) -> list[Annotated[int, "document id"]]:
        return [doc_id for doc_id, _ in self.__document_scores]
