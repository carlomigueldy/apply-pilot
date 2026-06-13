"""Schemas exposing runtime application settings to clients."""

from __future__ import annotations

from pydantic import BaseModel


class AppSettingsRead(BaseModel):
    """Public, non-sensitive view of the running app configuration."""

    app_env: str
    app_name: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    test_mode: bool
    provider_is_local: bool
