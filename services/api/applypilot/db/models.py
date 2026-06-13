"""SQLAlchemy 2.0 ORM models for ApplyPilot.

All models use the declarative ``Base`` from :mod:`applypilot.db.base`, UUID
primary keys (default :func:`uuid.uuid4`), ``func.now()`` server-side timestamps,
and ``ON DELETE CASCADE`` foreign keys so that deleting a parent row cleans up its
children at the database level.

Enum-typed columns (``type``, ``status``, ``category``, ``priority``, ...) are
stored as plain ``text`` to keep the schema flexible; the canonical string values
are enforced by the Pydantic layer (which is intentionally *not* imported here).

JSON metadata is exposed under the Python attribute names ``item_metadata`` /
``chunk_metadata`` / ``req_metadata`` to avoid shadowing SQLAlchemy's reserved
``metadata`` attribute, while still mapping to a DB column literally named
``metadata``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from applypilot.db.base import Base

# ---------------------------------------------------------------------------
# Reusable column mixins
# ---------------------------------------------------------------------------


class UUIDPKMixin:
    """Adds a UUID primary key defaulting to a freshly generated ``uuid4``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class CreatedAtMixin:
    """Adds a server-defaulted ``created_at`` timestamp."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    """Adds ``created_at`` plus an auto-updating ``updated_at`` timestamp."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Core identity & profile
# ---------------------------------------------------------------------------


class User(UUIDPKMixin, TimestampMixin, Base):
    """The single local-first user whose profile drives every application."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_salary_min_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_salary_max_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_tone: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile_items: Mapped[list[ProfileItem]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    job_applications: Mapped[list[JobApplication]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProfileItem(UUIDPKMixin, TimestampMixin, Base):
    """A unit of the user's career story (role, project, skill, achievement...)."""

    __tablename__ = "profile_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    item_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="profile_items")
    evidence_chunks: Mapped[list[EvidenceChunk]] = relationship(
        back_populates="profile_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EvidenceChunk(UUIDPKMixin, CreatedAtMixin, Base):
    """An embedded slice of a profile item used for semantic retrieval."""

    __tablename__ = "evidence_chunks"

    profile_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profile_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    profile_item: Mapped[ProfileItem] = relationship(back_populates="evidence_chunks")
    evidence_matches: Mapped[list[EvidenceMatch]] = relationship(
        back_populates="evidence_chunk",
        passive_deletes=True,
    )


# ---------------------------------------------------------------------------
# Job applications & analysis
# ---------------------------------------------------------------------------


class JobApplication(UUIDPKMixin, TimestampMixin, Base):
    """A single job the user is pursuing, plus its extracted job-post metadata."""

    __tablename__ = "job_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_job_post: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="saved")
    work_arrangement: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter_email: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="job_applications")
    requirements: Mapped[list[JobRequirement]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    evidence_matches: Mapped[list[EvidenceMatch]] = relationship(
        back_populates="application",
        passive_deletes=True,
    )
    fit_analyses: Mapped[list[FitAnalysis]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    drafts: Mapped[list[Draft]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    graph_runs: Mapped[list[GraphRun]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    review_decisions: Mapped[list[ReviewDecision]] = relationship(
        back_populates="application",
        passive_deletes=True,
    )


class JobRequirement(UUIDPKMixin, CreatedAtMixin, Base):
    """A single parsed requirement extracted from a job post."""

    __tablename__ = "job_requirements"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(Text, nullable=False)
    req_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    application: Mapped[JobApplication] = relationship(back_populates="requirements")
    evidence_matches: Mapped[list[EvidenceMatch]] = relationship(
        back_populates="requirement",
        passive_deletes=True,
    )


class EvidenceMatch(UUIDPKMixin, CreatedAtMixin, Base):
    """Links a job requirement to the profile evidence that satisfies it."""

    __tablename__ = "evidence_matches"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric, nullable=False)

    application: Mapped[JobApplication] = relationship(back_populates="evidence_matches")
    requirement: Mapped[JobRequirement] = relationship(back_populates="evidence_matches")
    evidence_chunk: Mapped[EvidenceChunk] = relationship(back_populates="evidence_matches")


class FitAnalysis(UUIDPKMixin, CreatedAtMixin, Base):
    """The synthesized fit assessment for an application."""

    __tablename__ = "fit_analyses"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    fit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    items: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    red_flags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    positioning_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    application: Mapped[JobApplication] = relationship(back_populates="fit_analyses")


# ---------------------------------------------------------------------------
# Drafts, graph runs & review trail
# ---------------------------------------------------------------------------


class Draft(UUIDPKMixin, TimestampMixin, Base):
    """A generated, reviewable piece of application content."""

    __tablename__ = "drafts"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="generated")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    length: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[JobApplication] = relationship(back_populates="drafts")
    review_decisions: Mapped[list[ReviewDecision]] = relationship(
        back_populates="draft",
        passive_deletes=True,
    )


class GraphRun(UUIDPKMixin, Base):
    """One execution of a LangGraph agent graph for an application."""

    __tablename__ = "graph_runs"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")
    current_node: Mapped[str | None] = mapped_column(Text, nullable=True)
    node_timings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )
    input_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    model_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    application: Mapped[JobApplication] = relationship(back_populates="graph_runs")


class ReviewDecision(UUIDPKMixin, CreatedAtMixin, Base):
    """A human-in-the-loop decision recorded against a draft."""

    __tablename__ = "review_decisions"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    draft_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drafts.id", ondelete="CASCADE"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[JobApplication] = relationship(back_populates="review_decisions")
    draft: Mapped[Draft] = relationship(back_populates="review_decisions")


__all__ = [
    "Base",
    "User",
    "ProfileItem",
    "EvidenceChunk",
    "JobApplication",
    "JobRequirement",
    "EvidenceMatch",
    "FitAnalysis",
    "Draft",
    "GraphRun",
    "ReviewDecision",
]
