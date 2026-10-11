import math
import re
import zlib

DIMENSIONS = 1536
FAKE_ANSWER = "Based on the documents [1]."
_REWRITE_PREFIX = "Rewrite the user's last question"


class FakeEmbeddingService:
    """Deterministic bag-of-words vectors: texts that share words are close."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    async def embed_text(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            vector[zlib.crc32(word.encode()) % DIMENSIONS] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class FakeLLMService:
    """Records every prompt it receives. Rewrite calls echo the question back."""

    def __init__(self) -> None:
        self.calls: list[list] = []

    async def complete(self, messages) -> str:
        self.calls.append(list(messages))
        if messages[0]["content"].startswith(_REWRITE_PREFIX):
            return messages[1]["content"].rsplit("Last question: ", 1)[1]
        return FAKE_ANSWER