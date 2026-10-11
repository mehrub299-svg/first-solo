from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatQuestion(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)
    # Only search these documents. Omitted, null or empty means all of them.
    document_ids: list[int] | None = Field(default=None, max_length=50)
    # Continue an existing chat. Omitted means start a new one.
    chat_id: int | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: int
    document_title: str
    chunk_index: int
    content: str
    score: float


class ChatAnswer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chat_id: int
    answer: str
    sources: list[SourceRead]


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[SourceRead] | None
    created_at: datetime