import math


from src.server.entities import DocumentInterface
from typing import Annotated, TypeAlias
from .invert_index import InvertIndexType

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
        self.__idfs_score: _TermIDFS = _TermIDFS()

    def __call__(
        self,
        query_terms: list[str],
        condidates_documents: list[DocumentInterface],
    ) -> list[tuple[Annotated[float, "document score"], DocumentInterface]]:
        chosen_documents: list[
            tuple[Annotated[float, "document score"], DocumentInterface]
        ] = list()
        # score the condidtate documents
        for document in condidates_documents:
            doc_score = self.__score_document(query_terms, document)
            chosen_documents.append((doc_score, document))
        # sort the document based on bm25 score
        chosen_documents.sort(key=lambda x: x[0], reverse=True)
        chosen_documents = chosen_documents[: self.__top_k]
        return chosen_documents

    def __score_document(
        self, query_terms: list[str], document: DocumentInterface
    ) -> float:
        score: float = 0.0
        for term in query_terms:
            if document.id not in self.__invert_index[term]:
                continue
            idf_score: float = self.__get_idf_score(term)
            _, term_frequency = self.__invert_index[term][document.id]
            tf_score: float = self.__tf(document.length, term_frequency)
            score += idf_score * tf_score
        return score

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        dominator: float = term_frequency + (
            self.__k
            * (1 - self.__b + (self.__b * (doc_len / self.__avg_document_length)))
        )
        return float(term_frequency / dominator)

    def __get_idf_score(self, term: str) -> float:
        if term not in self.__idfs_score.keys():
            number_of_document_contain_term: int = len(self.__invert_index[term])
            nominator: float = (
                self.__total_number_of_documents - number_of_document_contain_term + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            idf_term_score: float = math.log(nominator / dominator)
            self.__idfs_score[term] = idf_term_score
        return self.__idfs_score[term]
