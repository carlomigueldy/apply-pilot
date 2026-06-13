"""Liveness/readiness health endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from applypilot.core.config import get_settings
from applypilot.db.session import check_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health payload describing app identity, provider, and DB connectivity."""

    status: str
    app: str
    env: str
    llm_provider: str
    provider_is_local: bool
    db: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report service health including a live database connectivity probe."""
    settings = get_settings()
    db_ok = check_db()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        app=settings.app_name,
        env=settings.app_env,
        llm_provider=settings.llm_provider,
        provider_is_local=settings.provider_is_local,
        db="ok" if db_ok else "down",
    )
