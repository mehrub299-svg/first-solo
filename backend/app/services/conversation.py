from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, Message
from app.services.exceptions import ChatNotFound
from app.services.rag import HistoryTurn, RAGService
from app.services.retrieval import RetrievedChunk


@dataclass(frozen=True)
class ConversationAnswer:
    chat_id: int
    answer: str
    sources: list[RetrievedChunk]


class ConversationService:
    def __init__(
        self, session: AsyncSession, rag: RAGService, history_turns: int = 4
    ) -> None:
        self._session = session
        self._rag = rag
        self._history_turns = history_turns

    async def ask(
        self,
        user_id: int,
        question: str,
        top_k: int,
        document_ids: list[int] | None,
        chat_id: int | None,
    ) -> ConversationAnswer:
        chat = await self._get_chat(user_id, chat_id) if chat_id is not None else None
        history = await self._recent_history(chat.id) if chat is not None else []

        # Nothing is written until the answer succeeds.
        result = await self._rag.ask(user_id, question, top_k, document_ids, history)

        if chat is None:
            chat = Chat(user_id=user_id, title=self._title(question))
            self._session.add(chat)
            await self._session.flush()
        chat.updated_at = datetime.now(timezone.utc)
        self._session.add_all(
            [
                Message(chat_id=chat.id, role="user", content=question),
                Message(
                    chat_id=chat.id,
                    role="assistant",
                    content=result.answer,
                    sources=[asdict(source) for source in result.sources],
                ),
            ]
        )
        await self._session.commit()
        return ConversationAnswer(chat_id=chat.id, answer=result.answer, sources=result.sources)

    async def list_chats(self, user_id: int) -> list[Chat]:
        result = await self._session.execute(
            select(Chat)
            .where(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc(), Chat.id.desc())
        )
        return list(result.scalars().all())

    async def get_messages(self, user_id: int, chat_id: int) -> list[Message]:
        chat = await self._get_chat(user_id, chat_id)
        result = await self._session.execute(
            select(Message).where(Message.chat_id == chat.id).order_by(Message.id)
        )
        return list(result.scalars().all())

    async def delete_chat(self, user_id: int, chat_id: int) -> None:
        chat = await self._get_chat(user_id, chat_id)
        # Messages are removed by the database (ON DELETE CASCADE).
        await self._session.delete(chat)
        await self._session.commit()

    async def _get_chat(self, user_id: int, chat_id: int) -> Chat:
        result = await self._session.execute(
            select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()
        if chat is None:
            raise ChatNotFound()
        return chat

    async def _recent_history(self, chat_id: int) -> list[HistoryTurn]:
        result = await self._session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.id.desc())
            .limit(self._history_turns * 2)
        )
        messages = reversed(result.scalars().all())
        return [HistoryTurn(role=m.role, content=m.content) for m in messages]

    @staticmethod
    def _title(question: str) -> str:
        collapsed = " ".join(question.split())
        return collapsed if len(collapsed) <= 60 else collapsed[:59].rstrip() + "…"