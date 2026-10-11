from openai import AsyncOpenAI, OpenAIError

from app.services.exceptions import EmbeddingError


class EmbeddingService:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        dimensions: int,
        batch_size: int = 64,
    ) -> None:
        self._client = client
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors.extend(await self._embed_batch(batch))
        return vectors

    async def embed_text(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]

    async def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(
                model=self._model, input=batch
            )
        except OpenAIError as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc

        if not response.data or len(response.data) != len(batch):
            raise EmbeddingError("Embedding provider returned an unexpected response")

        ordered = sorted(response.data, key=lambda item: item.index)
        vectors = [item.embedding for item in ordered]
        for vector in vectors:
            if len(vector) != self._dimensions:
                raise EmbeddingError(
                    f"Expected {self._dimensions} dimensions, got {len(vector)}"
                )
        return vectors