import re


class ChunkingService:
    """Splits text into overlapping chunks, preferring paragraph/sentence/word breaks."""

    _SEPARATORS = ("\n\n", "\n", ". ", "? ", "! ", " ")

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        if chunk_size < 2:
            raise ValueError("chunk_size must be at least 2")
        if not 0 <= overlap < chunk_size // 2:
            raise ValueError("overlap must be >= 0 and < chunk_size // 2")
        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(self, text: str) -> list[str]:
        text = self._normalize(text)
        if not text:
            return []

        chunks: list[str] = []
        total = len(text)
        start = 0
        while start < total:
            end = min(start + self._chunk_size, total)
            if end < total:
                end = self._find_break(text, start, end)

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= total:
                break

            next_start = end - self._overlap
            if self._overlap:
                boundary = text.find(" ", next_start, end)
                if boundary != -1:
                    next_start = boundary + 1
            start = max(next_start, start + 1)
        return chunks

    def _find_break(self, text: str, start: int, end: int) -> int:
        lower = start + self._chunk_size // 2
        for separator in self._SEPARATORS:
            position = text.rfind(separator, lower, end)
            if position != -1:
                return position + len(separator)
        return end

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()