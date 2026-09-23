from typing import cast
from sentence_transformers import SentenceTransformer


class EmbedingModel:
    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        self.__model: SentenceTransformer = SentenceTransformer(model_name)

    def embed(self, chunk: str) -> list[float]:
        return cast(list[float], self.__model.encode(chunk).tolist())
