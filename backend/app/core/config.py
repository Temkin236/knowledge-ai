"""Application configuration module using Pydantic Settings."""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Knowledge AI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "Knowledge AI — RAG Assistant"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DATABASE_SYNC_URL: Optional[str] = None

    # Authentication & Supabase
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_JWT_SECRET: str = "dev-secret-key-change-in-production-min-32-chars"
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ALGORITHM: str = "HS256"
    DEV_MODE_AUTH: bool = True  # Allows local dev & offline testing without live Supabase

    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = None
    GENERATION_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768

    # Ingestion & Chunking
    CHUNK_SIZE: int = 800  # Target tokens (~3200 chars)
    CHUNK_OVERLAP: int = 120  # Overlap tokens (~480 chars)
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB

    # RAG Tuning
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.30
    MAX_CONTEXT_TOKENS: int = 4000
    ENABLE_QUERY_REFINEMENT: bool = True
    MAX_RETRIES: int = 1

    # Security & Networking
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    )
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


# Global settings singleton
settings = Settings()
