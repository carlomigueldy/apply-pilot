"""Synchronous SQLAlchemy 2.0 engine, session factory, and FastAPI dependency."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from applypilot.core.config import get_settings
from applypilot.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Synchronous engine. ``pool_pre_ping`` recycles dead connections transparently
# so a stale pooled connection does not surface as a request error.
engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

# ``expire_on_commit=False`` keeps ORM attributes usable after commit, which is
# convenient when returning objects from request handlers.
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_session() -> Generator[Session, None, None]:
    """Yield a request-scoped session, closing it when the request completes.

    Intended for use as a FastAPI dependency::

        def handler(session: Session = Depends(get_session)) -> ...:
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_db() -> bool:
    """Return ``True`` if the database answers a trivial ``SELECT 1``.

    Never raises: any connectivity or driver error is logged and reported as a
    ``False`` health result.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - health check must swallow all errors
        logger.exception("Database health check failed")
        return False
