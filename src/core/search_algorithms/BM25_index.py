import math


from src.server.entities import DocumentInterface
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
        invert_index: InvertIndexType,
    ) -> None:
        self.__k: float = k
        self.__b: float = b
        self.__top_k: int = top_k
        self.__avg_document_length: int = avg_documents_length
        self.__total_number_of_documents: int = total_number_of_documents
        self.__invert_index: InvertIndexType = invert_index

    def __call__(
        self, query_terms: list[str], condidates_documents: list[DocumentInterface]
    ) -> list[tuple[Annotated[float, "document score"], DocumentInterface]]:

        chosen_documents: list[
            tuple[Annotated[float, "document score"], DocumentInterface]
        ] = list()
        idfs_terms_score: _TermIDFS = self.__get_idf_terms(query_terms)
        for cond_doc in condidates_documents:
            doc_score = self.__score_document(query_terms, cond_doc, idfs_terms_score)
            chosen_documents.append((doc_score, cond_doc))
        chosen_documents.sort(key=lambda x: x[0], reverse=True)
        chosen_documents = chosen_documents[: self.__top_k]
        return chosen_documents

    def __score_document(
        self,
        query_terms: list[str],
        condidate_document: DocumentInterface,
        idfs_terms_score: _TermIDFS,
    ) -> float:
        score: float = 0.0
        for term in query_terms:
            idf_score: float = idfs_terms_score.get(term, 0.0)
            tf_score: float = self.__tf(
                condidate_document.length,
                self.__get_term_frequency_in_document(term, condidate_document.id),
            )
            score += idf_score * tf_score
        return score

    def __get_term_frequency_in_document(
        self, term_value: str, document_id: int
    ) -> int:
        frequency: int = 0
        postings: list[_Posting] = self.__invert_index[term_value]
        for term_frequency, document in postings:
            if document.id == document_id:
                frequency = term_frequency
                break
        return frequency

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        dominator: float = term_frequency + (
            self.__k
            * (1 - self.__b + (self.__b * (doc_len / self.__avg_document_length)))
        )
        return term_frequency / dominator

    def __get_idf_terms(self, query_terms: set[str]) -> _TermIDFS:
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
