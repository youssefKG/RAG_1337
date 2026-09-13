from src.server.entities import DocumentTermInterface, FileInterface, DocumentInterface
from src.core.search_algorithms.BM25_index import BM25Index


def test_bm25() -> None:
    bm25_search: BM25Index = BM25Index(
        document_term_repository=document_term_repository,
        document_repository=document_repository,
        top_k=10,
        query="""
    @staticmethod
    def _reshape_activation_tensor(
            x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        num = x.size(0)
        d = x.size(1) // 2
        x = x.reshape(num, 2, d)
        x1, x2 = torch.chunk(x, chunks=2, dim=1)
        x1 = x1.reshape(num, d)
        x2 = x2.reshape(num, d)
        return x1, x2 """,
    )
    bm25_search.search()
    condidate_documents = bm25_search.documents_score
    print(condidate_documents)
    documents: list[DocumentInterface] = document_repository.get_by_ids(
        condidate_documents
    )
    print(condidate_documents)
    for document in documents:
        print("document id: ", document.id)
        # print("document term value: ", document.value)
        # print("document frequency: ", document.frequency)
        print("file path: ", document.file.path)
        print("start_index: ", document.start_index)
        print("end_index: ", document.end_index)
