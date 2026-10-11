from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clients import get_openai_client
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.services.auth import AuthService
from app.services.chunking import ChunkingService
from app.services.conversation import ConversationService
from app.services.documents import DocumentService
from app.services.embedding import EmbeddingService
from app.services.exceptions import UserNotFound
from app.services.extraction import TextExtractor
from app.services.ingestion import IngestionService
from app.services.llm import LLMService
from app.services.rag import RAGService
from app.services.retrieval import RetrievalService
from app.services.tokens import TokenService

DbSession = Annotated[AsyncSession, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# --- auth ---------------------------------------------------------------


def get_token_service(db: DbSession) -> TokenService:
    settings = get_settings()
    return TokenService(
        db,
        refresh_ttl=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        reuse_grace=timedelta(seconds=settings.REFRESH_REUSE_GRACE_SECONDS),
    )


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_auth_service(db: DbSession, tokens: TokenServiceDep) -> AuthService:
    return AuthService(db, tokens)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], auth: AuthServiceDep
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    subject = decode_access_token(token)
    if subject is None or not subject.isdigit():
        raise credentials_error
    try:
        return await auth.get_user(int(subject))
    except UserNotFound:
        raise credentials_error


CurrentUser = Annotated[User, Depends(get_current_user)]


# --- knowledge services -------------------------------------------------


def get_chunking_service() -> ChunkingService:
    settings = get_settings()
    return ChunkingService(settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)


ChunkingServiceDep = Annotated[ChunkingService, Depends(get_chunking_service)]


def get_text_extractor() -> TextExtractor:
    return TextExtractor(get_settings().MAX_UPLOAD_BYTES)


TextExtractorDep = Annotated[TextExtractor, Depends(get_text_extractor)]


def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(
        get_openai_client(), settings.EMBEDDING_MODEL, settings.EMBEDDING_DIMENSIONS
    )


EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]


def get_llm_service() -> LLMService:
    settings = get_settings()
    return LLMService(
        get_openai_client(),
        settings.LLM_MODEL,
        settings.LLM_MAX_TOKENS,
        settings.LLM_TEMPERATURE,
    )


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]


def get_ingestion_service(
    db: DbSession,
    chunking: ChunkingServiceDep,
    embedding: EmbeddingServiceDep,
    extractor: TextExtractorDep,
) -> IngestionService:
    settings = get_settings()
    return IngestionService(
        db, chunking, embedding, extractor, settings.MAX_CHUNKS_PER_DOCUMENT
    )


IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]


def get_retrieval_service(
    db: DbSession, embedding: EmbeddingServiceDep
) -> RetrievalService:
    return RetrievalService(db, embedding)


RetrievalServiceDep = Annotated[RetrievalService, Depends(get_retrieval_service)]


def get_rag_service(retrieval: RetrievalServiceDep, llm: LLMServiceDep) -> RAGService:
    return RAGService(retrieval, llm)


RagServiceDep = Annotated[RAGService, Depends(get_rag_service)]


def get_conversation_service(db: DbSession, rag: RagServiceDep) -> ConversationService:
    return ConversationService(db, rag, get_settings().HISTORY_TURNS)


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


def get_document_service(db: DbSession) -> DocumentService:
    return DocumentService(db)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]