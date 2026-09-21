from server.repositories import DocumentRepositoryInterface


class HNSW:
    def __init__(self, document_repository: DocumentRepositoryInterface) -> None:
        self.__document_repository: DocumentRepositoryInterface = document_repository
        pass
