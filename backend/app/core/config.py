from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: str

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_REUSE_GRACE_SECONDS: int = 10
    COOKIE_SECURE: bool = False  # must be True when served over HTTPS

    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Never change the embedding model/dimensions once documents are stored.
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.2

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_CHUNKS_PER_DOCUMENT: int = 600
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    HISTORY_TURNS: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()