class Parser:
    def __init__(self) -> None:
        self.__max_chunk_size: int
        self.__search_query: str
        self.__top_k: int
        self.__data_set_path: str
        self.__project_content: str
