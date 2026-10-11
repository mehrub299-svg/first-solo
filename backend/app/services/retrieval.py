from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Chunk, Document
from app.services.embedding import EmbeddingService
from app.services.exceptions import DocumentNotFound


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    score: float  # cosine similarity: higher is more similar


class RetrievalService:
    def __init__(self, session: AsyncSession, embedding: EmbeddingService) -> None:
        self._session = session
        self._embedding = embedding

    async def search(
        self,
        user_id: int,
        query: str,
        top_k: int = 4,
        document_ids: Sequence[int] | None = None,
    ) -> list[RetrievedChunk]:
        selected = sorted(set(document_ids)) if document_ids else None
        if selected:
            # Validate before spending anything on embeddings.
            await self._ensure_owned(user_id, selected)

        query_vector = await self._embedding.embed_text(query)
        distance = Chunk.embedding.cosine_distance(query_vector)

        statement = (
            select(
                Chunk.document_id,
                Document.title,
                Chunk.chunk_index,
                Chunk.content,
                distance.label("distance"),
            )
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.user_id == user_id)  # per-user isolation
        )
        if selected:
            statement = statement.where(Chunk.document_id.in_(selected))
        statement = statement.order_by(distance).limit(top_k)

        result = await self._session.execute(statement)
        return [
            RetrievedChunk(
                document_id=row.document_id,
                document_title=row.title,
                chunk_index=row.chunk_index,
                content=row.content,
                score=1.0 - float(row.distance),
            )
            for row in result.all()
        ]

    async def _ensure_owned(self, user_id: int, document_ids: list[int]) -> None:
        result = await self._session.execute(
            select(func.count(Document.id)).where(
                Document.user_id == user_id, Document.id.in_(document_ids)
            )
        )
        if result.scalar_one() != len(document_ids):
            raise DocumentNotFound()