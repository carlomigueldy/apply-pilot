"""Alembic environment (synchronous).

Resolves the database URL from application settings at runtime, registers all
ORM models against ``Base.metadata`` so autogenerate sees every table, and runs
migrations using a synchronous engine (no async/await anywhere in the backend).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Importing the models module has the side effect of registering every mapped
# class on ``Base.metadata`` — keep this import even though it is not referenced
# directly, otherwise autogenerate would produce an empty diff.
from applypilot.core.config import get_settings
from applypilot.db import models as _models  # noqa: F401  (registers tables)
from applypilot.db.base import Base

# Alembic Config object, providing access to values in alembic.ini.
config = context.config

# Configure Python logging from the alembic.ini logging sections.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata that autogenerate compares the live database against.
target_metadata = Base.metadata


def _database_url() -> str:
    """Return the database URL sourced from application settings."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI connection)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live synchronous engine."""
    connectable = create_engine(
        _database_url(),
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
