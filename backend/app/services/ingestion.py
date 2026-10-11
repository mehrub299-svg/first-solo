import asyncio
from dataclasses import dataclass
from pathlib import PurePath

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Chunk, Document
from app.services.chunking import ChunkingService
from app.services.embedding import EmbeddingService
from app.services.exceptions import DocumentTooLarge, EmptyDocument
from app.services.extraction import TextExtractor


@dataclass(frozen=True)
class IngestionResult:
    document: Document
    chunk_count: int


class IngestionService:
    def __init__(
        self,
        session: AsyncSession,
        chunking: ChunkingService,
        embedding: EmbeddingService,
        extractor: TextExtractor,
        max_chunks: int = 600,
    ) -> None:
        self._session = session
        self._chunking = chunking
        self._embedding = embedding
        self._extractor = extractor
        self._max_chunks = max_chunks

    async def ingest_file(
        self, user_id: int, title: str | None, filename: str, data: bytes
    ) -> IngestionResult:
        text = await asyncio.to_thread(self._extractor.extract, filename, data)
        resolved = (title or "").strip() or PurePath(filename).stem.strip() or "Untitled"
        return await self.ingest(user_id, resolved[:255], text)

    async def ingest(self, user_id: int, title: str, text: str) -> IngestionResult:
        pieces = self._chunking.split(text)
        if not pieces:
            raise EmptyDocument()
        if len(pieces) > self._max_chunks:
            raise DocumentTooLarge(
                f"Document is too large ({len(pieces)} passages, the limit is {self._max_chunks})."
            )

        # Embed first, so no database transaction stays open during the API call.
        vectors = await self._embedding.embed_texts(pieces)

        try:
            document = Document(user_id=user_id, title=title.strip())
            self._session.add(document)
            await self._session.flush()
            self._session.add_all(
                [
                    Chunk(
                        document_id=document.id,
                        user_id=user_id,
                        chunk_index=index,
                        content=content,
                        embedding=vector,
                    )
                    for index, (content, vector) in enumerate(zip(pieces, vectors))
                ]
            )
            await self._session.commit()
        except SQLAlchemyError:
            await self._session.rollback()
            raise

        await self._session.refresh(document)
        return IngestionResult(document=document, chunk_count=len(pieces))