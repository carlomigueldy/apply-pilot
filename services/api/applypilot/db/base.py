"""Declarative base with an Alembic-friendly constraint naming convention."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Deterministic constraint/index names make Alembic autogenerate migrations
# stable across runs and across databases.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models.

    Models live in ``applypilot.db.models`` (owned by another module) and inherit
    from this class so they share a single ``MetaData`` with consistent
    constraint naming.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
