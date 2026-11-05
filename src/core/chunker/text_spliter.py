import re
from typing import Annotated
from .languages import Language
from .separators import PYTHON_SEPARATORS, MARKDOWN_SPERATORS, TEXT_SEPARATORS


class TextSpliter:
    def __init__(
        self,
        /,
        *,
        source: str,
        language: Language,
        max_chunk_size: int = 2000,
    ) -> None:
        self._max_chunk_size: int = max_chunk_size
        self._language: Language = language
        self._source: str = source

    def split_text(
        self,
    ) -> list[
        tuple[
            Annotated[str, "chunk"],
            Annotated[int, "start index"],
            Annotated[int, "end index"],
        ]
    ]:
        return [
            self.__form_chunk(chunk)
            for chunk in self._split_text(self._source, self.__get_separators)
        ]

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        chunks: list[str] = list()
        separator: str = separators[-1]
        new_separators: list[str] = list()
        merged_splits: list[str]
        for i, s_ in enumerate(separators):
            if not s_:
                separator = s_
                break
            if re.search(s_, text):
                separator = s_
                new_separators = separators[i + 1:]
                break
        splited_text: list[str] = self._split_text_with_regex(text, separator)
        good_splits: list[str] = list()
        for s in splited_text:
            if len(s) < self._max_chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    merged_splits = self._merge_splits(good_splits, separator)
                    chunks.extend(merged_splits)
                    good_splits = []
                if not new_separators:
                    chunks.append(s)
                else:
                    other: list[str] = self._split_text(s, new_separators)
                    chunks.extend(other)
        if good_splits:
            merged_splits = self._merge_splits(good_splits, separator)
            chunks.extend(merged_splits)
        return chunks

    def _split_text_with_regex(self, text: str, separator: str) -> list[str]:
        text_parts: list[str]
        if separator:
            text_parts = re.split(f"({separator})", text)
        else:
            text_parts = list(text)
        return [s for s in text_parts if s]

    def _merge_splits(self, good_splits: list[str], sep: str) -> list[str]:
        merged_splits: list[str] = list()
        total: int = 0
        sep_len = len(sep)
        current_merged_text: list[str] = list()
        for doc in good_splits:
            doc_len: int = len(doc)
            if (
                doc_len
                + total
                + (sep_len if current_merged_text else 0)
             ) >= self._max_chunk_size:
                text: str = "".join(current_merged_text)
                merged_splits.append(text)
                total = 0
                current_merged_text.clear()
            total += doc_len + (sep_len if current_merged_text else 0)
            current_merged_text.append(doc)
        merged_splits.append("".join(current_merged_text))
        return merged_splits

    def __form_chunk(self, chunk: str) -> tuple[
        Annotated[str, "chunk"],
        Annotated[int, "start index"],
        Annotated[int, "end index"],
    ]:
        start: int = self._source.find(chunk)
        end: int = start + len(chunk)
        return (chunk, start, end)

    @property
    def __get_separators(self) -> list[str]:
        match self._language:
            case Language.PYTHON:
                return PYTHON_SEPARATORS
            case Language.MARKDOWN:
                return MARKDOWN_SPERATORS
            case Language.TEXT:
                return TEXT_SEPARATORS
