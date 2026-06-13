"""Draft repository: CRUD, versioning, and status helpers for Draft records."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from applypilot.db.models import Draft


class DraftRepository:
    """CRUD, versioning, and status management for :class:`~applypilot.db.models.Draft`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        application_id: uuid.UUID,
        type: str,  # noqa: A002
        title: str,
        body: str,
        status: str = "generated",
        version: int | None = None,
        tone: str | None = None,
        length: str | None = None,
        review_notes: str | None = None,
    ) -> Draft:
        """Persist a new draft.

        When *version* is omitted, :meth:`next_version` is called automatically
        so that draft revisions for the same application + type are numbered
        consecutively without gaps.
        """
        if version is None:
            version = self.next_version(application_id, type)
        draft = Draft(
            application_id=application_id,
            type=type,
            title=title,
            body=body,
            status=status,
            version=version,
            tone=tone,
            length=length,
            review_notes=review_notes,
        )
        self.session.add(draft)
        self.session.flush()
        return draft

    def get(self, draft_id: uuid.UUID) -> Draft | None:
        """Return the draft with *draft_id*, or ``None``."""
        stmt = select(Draft).where(Draft.id == draft_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_application(
        self,
        application_id: uuid.UUID,
        type: str | None = None,  # noqa: A002
    ) -> Sequence[Draft]:
        """Return drafts for an application, newest version first.

        Optionally filter to a specific draft *type*.
        """
        stmt = (
            select(Draft)
            .where(Draft.application_id == application_id)
            .order_by(Draft.version.desc(), Draft.created_at.desc())
        )
        if type is not None:
            stmt = stmt.where(Draft.type == type)
        return self.session.execute(stmt).scalars().all()

    def update(self, draft_id: uuid.UUID, **kwargs: Any) -> Draft | None:
        """Apply *kwargs* as attribute updates; return the updated draft or ``None``."""
        draft = self.get(draft_id)
        if draft is None:
            return None
        for key, value in kwargs.items():
            setattr(draft, key, value)
        self.session.flush()
        return draft

    def delete(self, draft_id: uuid.UUID) -> bool:
        """Delete the draft; return ``True`` if it existed."""
        draft = self.get(draft_id)
        if draft is None:
            return False
        self.session.delete(draft)
        self.session.flush()
        return True

    def next_version(self, application_id: uuid.UUID, type: str) -> int:  # noqa: A002
        """Return the next sequential version number for a given application + type.

        Returns ``1`` when no prior draft of this type exists for the application.
        """
        stmt = select(func.max(Draft.version)).where(
            Draft.application_id == application_id,
            Draft.type == type,
        )
        result = self.session.execute(stmt).scalar()
        return (result or 0) + 1

    def set_status(self, draft_id: uuid.UUID, status: str) -> Draft | None:
        """Update *draft_id*'s status field; return the updated draft or ``None``."""
        draft = self.get(draft_id)
        if draft is None:
            return None
        draft.status = status
        self.session.flush()
        return draft
