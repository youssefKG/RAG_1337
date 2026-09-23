from typing import cast
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    PreTrainedTokenizerBase,
    PreTrainedModel,
)
from sentence_transformers import SentenceTransformer


class LLM:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        embeding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.__device: str
        self.__tokenizer: PreTrainedTokenizerBase
        self.__model_name: str = model_name
        self.__embeding_model_name: str = embeding_model
        if torch.backends.mps.is_available():
            self.__device = "mps"
        elif torch.cuda.is_available():
            self.__device = "cuda"
        else:
            self.__device = "cpu"
        self.__embeding_model: SentenceTransformer = SentenceTransformer(
            self.__embeding_model_name
        )
        # self.__model: PreTrainedModel = cast(
        #     PreTrainedModel,
        #     cast(
        #         object,
        #         AutoModelForCausalLM.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
        #             self.__model_name, dtype="auto", device_map=self.__device
        #         ),
        #     ),
        # )
        # self.__tokenizer = cast(
        #     PreTrainedTokenizerBase,
        #     cast(
        #         object,
        #         AutoTokenizer.from_pretrained(  # pyright: ignore[reportUnknownMemberType]
        #             self.__model_name, trust_remote_code=True
        #         ),
        #     ),
        # )

    # def encode(self, text: str) -> torch.Tensor:
    #     ids = self.__tokenizer(text, add_special_tokens=False)
    #     print(ids)
    #     return torch.Tensor([ids], device=self.__device)
    #
    # def decode(self, ids: torch.Tensor) -> str:
    #     return cast(
    #         str, cast(object, self.__tokenizer.decode(ids, skip_sepecial_tokens=True))
    #     )

    def embed(self, text: str) -> list[float]:
        return cast(
            list[float], cast(object, self.__embeding_model.encode(text).tolist())
        )


if __name__ == "__main__":
    sentences = [
        "Hugging Face makes NLP easy.",
        "Transformers are powerful for deep learning.",
        "Hugging Face makes NLP easy.",
        "Transformers are powerful for deep learning.",
        "Hugging Face makes NLP easy.",
        "Transformers are powerful for deep learning.",
        "Hugging Face makes NLP easy.",
        "Transformers are powerful for deep learning.",
        "Hugging Face makes NLP easy.",
    ]
    model: LLM = LLM()
    data = model.embed(sentences)
    print(data)
