"""Shared pytest fixtures for the ApplyPilot test suite.

Fixture hierarchy
-----------------
test_engine (session-scoped)
    └─ db_session (function-scoped) — truncates all tables after each test
           └─ client (function-scoped) — FastAPI TestClient with get_session overridden

Settings override
-----------------
Environment variables are set at module import time so that Settings picks them
up before the first call to get_settings().  The lru_cache is cleared here so
any previously cached instance is discarded.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Override settings BEFORE any applypilot module that caches settings is imported.
# ---------------------------------------------------------------------------
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot_test",
)

_TEST_DB_URL: str = os.environ["TEST_DATABASE_URL"]

# Force test-safe provider values; clear the lru_cache so the overrides take effect.
os.environ["LLM_PROVIDER"] = "fake"
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ["TEST_MODE"] = "true"

from applypilot.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import applypilot.db.models  # noqa: E402, F401 — side-effect import: registers ORM models
from applypilot.db.base import Base  # noqa: E402
from applypilot.db.session import get_session  # noqa: E402
from applypilot.main import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Session-scoped engine — created once per pytest run.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_engine():
    """Create a SQLAlchemy engine pointing at the TEST database.

    Also ensures the ``pgvector`` extension is installed and runs
    ``Base.metadata.create_all`` to create all tables.
    """
    engine = create_engine(_TEST_DB_URL, pool_pre_ping=True, future=True)

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


# ---------------------------------------------------------------------------
# Function-scoped DB session — truncates tables after each test.
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session(test_engine) -> Session:
    """Yield a sync Session bound to the test engine.

    All tables are truncated after the test completes so each test starts with
    a clean slate.  Foreign-key checks are temporarily disabled via the
    ``session_replication_role`` trick so truncation order does not matter.
    """
    factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()
        # Truncate all tables between tests.
        with test_engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()


# ---------------------------------------------------------------------------
# FastAPI TestClient with overridden session dependency.
# ---------------------------------------------------------------------------


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Return a synchronous TestClient that uses *db_session* for every request.

    The ``get_session`` FastAPI dependency is overridden so all route handlers
    share the same test session, enabling assertions on DB state after HTTP calls.
    """
    app = create_app()
    # Clear any stale settings cache so test env-vars take effect inside the app.
    get_settings.cache_clear()

    def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
