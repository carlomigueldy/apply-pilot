"""Application settings route.

Exposes a single GET endpoint that returns the public, non-sensitive subset of
the running application's configuration so clients can adapt their behaviour
(e.g. show a "local mode" badge when the LLM provider runs offline).
"""

from __future__ import annotations

from fastapi import APIRouter

from applypilot.core.config import get_settings
from applypilot.schemas.settings import AppSettingsRead

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsRead)
def get_app_settings() -> AppSettingsRead:
    """Return the public, non-sensitive application configuration."""
    cfg = get_settings()
    return AppSettingsRead(
        app_env=cfg.app_env,
        app_name=cfg.app_name,
        llm_provider=cfg.llm_provider,
        llm_model=cfg.llm_model,
        embedding_provider=cfg.embedding_provider,
        embedding_model=cfg.embedding_model,
        test_mode=cfg.test_mode,
        provider_is_local=cfg.provider_is_local,
    )
