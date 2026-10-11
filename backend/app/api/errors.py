import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import (
    ChatNotFound,
    DocumentNotFound,
    DocumentTooLarge,
    EmbeddingError,
    EmptyDocument,
    FileTooLarge,
    LLMError,
    UnreadableFile,
    UnsupportedFileType,
)

logger = logging.getLogger("app.errors")


def _make_handler(status_code: int, detail: str | None = None, log: bool = False):
    """detail=None passes the exception's own (user-safe) message through."""

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        if log:
            logger.error("%s: %s", type(exc).__name__, exc)
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail if detail is not None else str(exc)},
        )

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EmptyDocument, _make_handler(422, "Document has no readable text"))
    app.add_exception_handler(DocumentTooLarge, _make_handler(413))
    app.add_exception_handler(DocumentNotFound, _make_handler(404, "Document not found"))
    app.add_exception_handler(ChatNotFound, _make_handler(404, "Chat not found"))
    app.add_exception_handler(FileTooLarge, _make_handler(413))
    app.add_exception_handler(UnsupportedFileType, _make_handler(415))
    app.add_exception_handler(UnreadableFile, _make_handler(422))
    app.add_exception_handler(
        EmbeddingError, _make_handler(502, "Embedding provider error", log=True)
    )
    app.add_exception_handler(
        LLMError, _make_handler(502, "Language model provider error", log=True)
    )