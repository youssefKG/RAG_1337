import math


from src.server.entities import DocumentTermInterface
from src.server.repositories import (
    DocumentRepositoryInterface,
    DocumentTermRepositoryInterface,
)
from typing import Annotated


class BM25Index:
    def __init__(
        self,
        *,
        k: float = 1.2,
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
        # self.__conditate_documents: set[int] = {
        #     doc_term.document.id for doc_term in self.__document_terms
        # }
        self.__document_scores: list[
            tuple[Annotated[int, "document id"], Annotated[float, "document score"]]
        ] = list()
        self.__terms_idfs: dict[
            Annotated[str, "term value"], Annotated[float, "idf(t) score"]
        ] = dict()
        self.__init_idf_terms()

    def search(
        self,
    ) -> None:
        score: float = 0.0
        passed_ids: set[int] = set()
        for doc in self.__document_terms:
            if doc.document.id not in passed_ids:
                for term_value in self.__query_terms:
                    document_term: DocumentTermInterface | None = (
                        self.get_document_term(doc.document.id, term_value)
                    )
                    if (
                        document_term is None
                        or term_value not in self.__terms_idfs.keys()
                    ):
                        continue
                    score += self.__terms_idfs[term_value] * self.__tf(document_term)
                self.__document_scores.append((doc.document.id, score))
                # print(
                #     f"{len(self.__document_scores)}/{len(self.__conditate_documents)}"
                # )
                passed_ids.add(doc.document.id)
                score = 0.0
        # self.__document_scores.sort(key=lambda element: element[1], reverse=True)
        if len(self.__document_scores) > self.__top_k:
            self.__document_scores = self.__document_scores[: self.__top_k]
        print("document scores: ", self.__document_scores)

    def __tf(self, document_term: DocumentTermInterface) -> float:
        doc_len: int = document_term.document.length
        tf: int = document_term.frequency
        dominator: float = tf + self.__k * (
            1 - self.__b + (self.__b * (doc_len / self.__avg_document_length))
        )
        return tf / dominator

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

    def __init_idf_terms(self) -> None:
        for term in self.__query_terms:
            number_of_document_contain_term: int = (
                self.__get_number_of_documents_contain_term(term)
            )
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

    def __get_number_of_documents_contain_term(self, term: str) -> int:
        return sum(
            [1 if doc_term.value == term else 0 for doc_term in self.__document_terms]
        )
