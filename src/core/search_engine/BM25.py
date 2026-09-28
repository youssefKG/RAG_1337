from dataclasses import dataclass
from typing import Annotated, TypeAlias
import math

from src.core.entities import Document
from .invert_index import InvertIndexType, PostingType

_TermIDFS: TypeAlias = dict[
    Annotated[str, "term value"], Annotated[float, "idf(t) score"]
]


@dataclass(frozen=False)
class DocumentScore:
    document: Document
    score: float = 0


_DocumentScoreType: TypeAlias = dict[Annotated[str, "document id"], DocumentScore]


class BM25:
    def __init__(
        self,
        *,
        k: float = 1.2,
        b: float = 0.75,
        avg_documents_length: float,
        total_number_of_documents: int,
        invert_index: InvertIndexType,
    ) -> None:
        self.__k: float = k
        self.__b: float = b
        self.__avg_document_length: float = avg_documents_length
        self.__total_number_of_documents: int = total_number_of_documents
        self.__invert_index: InvertIndexType = invert_index
        self.__idfs_score: _TermIDFS = _TermIDFS()

    def __call__(self, query_terms: list[str], top_k: int, ) -> list[Document]:
        chosen_documents: _DocumentScoreType = _DocumentScoreType()
        for term in query_terms:
            if term in self.__invert_index:
                posting: PostingType = self.__invert_index[term]
                for document_id, (document, term_frequency) in posting.items():
                    if document_id not in chosen_documents:
                        chosen_documents[document_id] = DocumentScore(
                            document=document, score=0
                        )
                    chosen_documents[document_id].score += self.__score_document(
                        document, term, term_frequency, len(posting)
                    )
        high_score_document: list[DocumentScore] = sorted(
            chosen_documents.values(), key=lambda x: x.score, reverse=True
        )[:top_k]
        return [doc.document for doc in high_score_document]

    def __score_document(
        self,
        document: Document,
        term: str,
        term_frequency: int,
        number_of_document_contain_term: int,
    ) -> float:
        idf_score: float = self.__get_idf_score(term, number_of_document_contain_term)
        tf_score: float = self.__tf(document.length, term_frequency)
        return tf_score * idf_score

    def __tf(self, doc_len: int, term_frequency: int) -> float:
        nominator: float = term_frequency * (self.__k + 1)
        dominator: float = term_frequency + (
            self.__k
            * (1 - self.__b + (self.__b * (doc_len / self.__avg_document_length)))
        )
        return float(nominator / dominator)

    def __get_idf_score(self, term: str, number_of_document_contain_term: int) -> float:
        if term not in self.__idfs_score:
            nominator: float = (
                self.__total_number_of_documents - number_of_document_contain_term + 0.5
            )
            dominator: float = number_of_document_contain_term + 0.5
            idf_term_score: float = math.log(nominator / dominator)
            self.__idfs_score[term] = idf_term_score
        return self.__idfs_score[term]
