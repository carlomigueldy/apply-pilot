"""Evidence repositories: EvidenceMatch and FitAnalysis."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import EvidenceMatch, FitAnalysis


class EvidenceMatchRepository:
    """Bulk-create and listing for :class:`~applypilot.db.models.EvidenceMatch`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def bulk_create(self, matches: list[dict[str, Any]]) -> list[EvidenceMatch]:
        """Persist a batch of evidence matches from a list of attribute dicts.

        Each dict must contain at minimum ``application_id``, ``requirement_id``,
        ``evidence_chunk_id``, ``summary``, and ``confidence``.
        """
        objects = [EvidenceMatch(**match) for match in matches]
        self.session.add_all(objects)
        self.session.flush()
        return objects

    def list_by_application(
        self, application_id: uuid.UUID
    ) -> Sequence[EvidenceMatch]:
        """Return all evidence matches for a given application."""
        stmt = select(EvidenceMatch).where(
            EvidenceMatch.application_id == application_id
        )
        return self.session.execute(stmt).scalars().all()


class FitAnalysisRepository:
    """Create and query :class:`~applypilot.db.models.FitAnalysis` records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        application_id: uuid.UUID,
        fit_score: int,
        summary: str,
        items: list[Any] | None = None,
        red_flags: list[Any] | None = None,
        positioning_strategy: str | None = None,
        raw_output: dict[str, Any] | None = None,
    ) -> FitAnalysis:
        """Persist a new fit analysis record and flush."""
        analysis = FitAnalysis(
            application_id=application_id,
            fit_score=fit_score,
            summary=summary,
            items=items or [],
            red_flags=red_flags or [],
            positioning_strategy=positioning_strategy,
            raw_output=raw_output,
        )
        self.session.add(analysis)
        self.session.flush()
        return analysis

    def get_latest_by_application(
        self, application_id: uuid.UUID
    ) -> FitAnalysis | None:
        """Return the most-recently created fit analysis for *application_id*.

        Returns ``None`` when no analysis has been run for the application yet.
        """
        stmt = (
            select(FitAnalysis)
            .where(FitAnalysis.application_id == application_id)
            .order_by(FitAnalysis.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()
