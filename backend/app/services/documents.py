from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Chunk, Document
from app.services.exceptions import DocumentNotFound


@dataclass(frozen=True)
class DocumentSummary:
    id: int
    title: str
    created_at: datetime
    chunk_count: int


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_documents(self, user_id: int) -> list[DocumentSummary]:
        statement = (
            select(
                Document.id,
                Document.title,
                Document.created_at,
                func.count(Chunk.id).label("chunk_count"),
            )
            .select_from(Document)
            .outerjoin(Chunk, Chunk.document_id == Document.id)
            .where(Document.user_id == user_id)
            .group_by(Document.id)
            .order_by(Document.created_at.desc(), Document.id.desc())
        )
        result = await self._session.execute(statement)
        return [
            DocumentSummary(
                id=row.id,
                title=row.title,
                created_at=row.created_at,
                chunk_count=row.chunk_count,
            )
            for row in result.all()
        ]

    async def delete_document(self, user_id: int, document_id: int) -> None:
        document = await self._session.get(Document, document_id)
        if document is None or document.user_id != user_id:
            raise DocumentNotFound()
        # Chunks are removed by the database (ON DELETE CASCADE).
        await self._session.delete(document)
        await self._session.commit()