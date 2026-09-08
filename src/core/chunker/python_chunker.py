from .text_spliter import TextSpliter
from .separators import PYTHON_SEPARATORS


class PythonChunker(TextSpliter):
    def ___init__(
        self,
        *,
        separators: list[str],
        source: str = "",
        overlap_size: int = 0,
        max_chunk_size: int = 200,
    ) -> None:
        super().__init__(
            max_chunk_size=max_chunk_size,
            source=source,
            overlap_size=overlap_size,
            separators=PYTHON_SEPARATORS,
        )
