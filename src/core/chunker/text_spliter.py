import re
from typing import Annotated
from .languages import Language
from .separators import PYTHON_SEPARATORS, MARKDOWN_SPERATORS, TEXT_SEPARATORS


class TextSpliter:
    def __init__(
        self,
        /,
        *,
        language: Language,
        max_chunk_size: int = 290,
        overlap_size: int = 1000,
        source: str = "",
    ) -> None:
        self._max_chunk_size: int = max_chunk_size
        self._language: Language = language
        self._overlap_size: int = overlap_size
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

    def _merge_splits(self, splits: list[str], sep: str) -> list[str]:
        merged_splits: list[str] = list()
        sep_len: int = len(sep)
        current_merged_texts: list[str] = list()
        total: int = 0
        for s in splits:
            s_len = len(s)
            if (
                s_len
                + total
                + (sep_len if len(current_merged_texts) > 0 else 0)
                >= self._max_chunk_size
            ):
                if len(current_merged_texts) > 0:
                    txt: str = "".join(current_merged_texts)
                    merged_splits.append(txt)
                    while total > self._overlap_size or (
                        total
                        + s_len
                        + (len(sep) if len(current_merged_texts) else 0)
                        > self._max_chunk_size
                        and total > 0
                    ):
                        total -= len(current_merged_texts[0]) + (
                            sep_len if len(current_merged_texts) > 1 else 0
                        )
                        current_merged_texts = current_merged_texts[1:]
            current_merged_texts.append(s)
            total += s_len + (sep_len if len(current_merged_texts) > 1 else 0)
        merged_splits.append("".join(current_merged_texts))
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


class MyTextSpliter:
    def __init__(self, max_chunk_size: int, separators: list[str]) -> None:
        self.__max_chunk_size: int = max_chunk_size
        self.__seprators: list[str] = separators

    def split_text(self, text: str, separators: list[str]) -> list[str]:
        good_chunks: list[str] = list()
        chunks: list[str] = list()
        seperator: str = separators[-1]
        new_separators: list[str] = list()
        for idx, sep in enumerate(separators):
            if sep:
                seperator = sep
                new_separators = separators[idx + 1:]
                break
            elif re.search(text, sep):
                seperator = sep
                new_separators = separators[idx + 1: ]
                break
        for doc in self.__split_text_with_regex(text, seperator):
            if len(doc) < self.__max_chunk_size:
                good_chunks.append(doc)
            else:
                if good_chunks:
                    other: list[str] = self.__merge(good_chunks, seperator)
                    good_chunks = []
                    chunks.extend(other)
                if new_separators:
                    other: list[str] = self.split_text(doc, new_seperator)
                    good_chunks.append(doc)

    def __split_text_with_regex(self,  text: str, sep: str) -> list[str]:
        if sep:
            return re.split(f"({sep})", text)
        return list(text)

    def __merge(self, good_splits: list[str], seperators: str) -> list[str]:
        return list()

