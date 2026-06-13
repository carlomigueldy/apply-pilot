"""Shared FastAPI dependencies for route handlers.

Re-exports the request-scoped database :func:`get_session` dependency and
provides a cached application-settings dependency. Both are synchronous.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from applypilot.core.config import Settings, get_settings
from applypilot.db.session import get_session

__all__ = ["SessionDep", "SettingsDep", "get_app_settings", "get_session"]


def get_app_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance."""
    return get_settings()


# Annotated dependency aliases for concise handler signatures.
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
