from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TeloHive Venue Knowledge API"
    ENV: str = "local"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/venue_knowledge"
    LOG_LEVEL: str = "INFO"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    RETRIEVAL_TOP_K: int = 5
    MIN_RELEVANCE_SCORE: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
