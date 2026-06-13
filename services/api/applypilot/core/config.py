"""Application configuration loaded from the environment via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Providers considered "local" — no external network calls / API keys required.
LOCAL_LLM_PROVIDERS: frozenset[str] = frozenset({"fake", "ollama"})


class Settings(BaseSettings):
    """Strongly-typed application settings sourced from environment variables.

    Values are read from ``.env.local`` then ``.env`` (first wins), and finally
    the process environment. Field names map to uppercase env var names because
    ``case_sensitive`` is disabled.
    """

    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_env: str = "local"
    app_name: str = "ApplyPilot"
    web_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # --- Datastores ---
    database_url: str = (
        "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot"
    )
    redis_url: str = "redis://localhost:6379/0"

    # --- Object storage ---
    storage_driver: str = "minio"
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "applypilot"
    minio_secret_key: str = "applypilot"
    minio_bucket: str = "applypilot"

    # --- LLM provider ---
    llm_provider: str = "fake"
    llm_model: str = "fake-applypilot-v1"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # --- Embedding provider ---
    embedding_provider: str = "fake"
    embedding_model: str = "fake-embedding-v1"

    # --- Observability ---
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str | None = None

    # --- Behaviour flags ---
    test_mode: bool = False
    seed_demo_data: bool = True

    @property
    def provider_is_local(self) -> bool:
        """Whether the configured LLM provider runs locally (no external API)."""
        return self.llm_provider.strip().lower() in LOCAL_LLM_PROVIDERS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()
