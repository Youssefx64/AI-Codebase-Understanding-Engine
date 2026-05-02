"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Codebase Understanding Engine"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (PostgreSQL)
    database_url: Optional[str] = None
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600  # 1 hour

    # Neo4j
    neo4j_uri: Optional[str] = None
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # Vector DB (ChromaDB)
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "codebase_chunks"

    # OpenAI / LLM
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Repository storage
    repos_base_dir: str = "./data/repos"
    max_repo_size_mb: int = 500

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # JWT Auth
    jwt_secret: str = "change-me-in-production-use-a-long-random-secret"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    @property
    def effective_openai_api_key(self) -> str:
        """Get the effective OpenAI API key, preferring AI integration."""
        import os
        return (
            os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
            or self.openai_api_key
            or "sk-placeholder"
        )

    @property
    def effective_openai_base_url(self) -> Optional[str]:
        """Get the effective OpenAI base URL, preferring AI integration."""
        import os
        return (
            os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
            or self.openai_base_url
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
