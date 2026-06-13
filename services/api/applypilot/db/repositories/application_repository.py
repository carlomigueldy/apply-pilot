"""Application-domain repositories: JobApplication and JobRequirement."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from applypilot.db.models import FitAnalysis, JobApplication, JobRequirement


class JobApplicationRepository:
    """CRUD operations for :class:`~applypilot.db.models.JobApplication`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: uuid.UUID,
        raw_job_post: str,
        **kwargs: Any,
    ) -> JobApplication:
        """Persist a new job application and flush to assign a DB-generated id."""
        application = JobApplication(
            user_id=user_id,
            raw_job_post=raw_job_post,
            **kwargs,
        )
        self.session.add(application)
        self.session.flush()
        return application

    def get(self, application_id: uuid.UUID) -> JobApplication | None:
        """Return the application with *application_id*, or ``None``."""
        stmt = select(JobApplication).where(JobApplication.id == application_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(
        self, user_id: uuid.UUID, status: str | None = None
    ) -> Sequence[JobApplication]:
        """Return all applications for *user_id*, optionally filtered by *status*."""
        stmt = (
            select(JobApplication)
            .where(JobApplication.user_id == user_id)
            .order_by(JobApplication.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(JobApplication.status == status)
        return self.session.execute(stmt).scalars().all()

    def update(
        self, application_id: uuid.UUID, **kwargs: Any
    ) -> JobApplication | None:
        """Apply *kwargs* as attribute updates; return the updated object or ``None``."""
        application = self.get(application_id)
        if application is None:
            return None
        for key, value in kwargs.items():
            setattr(application, key, value)
        self.session.flush()
        return application

    def delete(self, application_id: uuid.UUID) -> bool:
        """Delete the application; return ``True`` if it existed."""
        application = self.get(application_id)
        if application is None:
            return False
        self.session.delete(application)
        self.session.flush()
        return True

    def list_with_fit_summary(
        self, user_id: uuid.UUID
    ) -> Sequence[tuple[JobApplication, FitAnalysis | None]]:
        """Return applications with their latest fit analysis, or ``None`` if absent.

        Uses a subquery to identify the most-recent
        :class:`~applypilot.db.models.FitAnalysis` per application, then
        outer-joins that row into the result set.
        """
        latest_sq = (
            select(
                FitAnalysis.application_id,
                func.max(FitAnalysis.created_at).label("max_created_at"),
            )
            .group_by(FitAnalysis.application_id)
            .subquery()
        )
        stmt = (
            select(JobApplication, FitAnalysis)
            .outerjoin(
                latest_sq,
                JobApplication.id == latest_sq.c.application_id,
            )
            .outerjoin(
                FitAnalysis,
                (FitAnalysis.application_id == latest_sq.c.application_id)
                & (FitAnalysis.created_at == latest_sq.c.max_created_at),
            )
            .where(JobApplication.user_id == user_id)
            .order_by(JobApplication.created_at.desc())
        )
        rows = self.session.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]


class JobRequirementRepository:
    """CRUD operations for :class:`~applypilot.db.models.JobRequirement`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        application_id: uuid.UUID,
        text: str,
        category: str,
        priority: str,
        req_metadata: dict[str, Any] | None = None,
    ) -> JobRequirement:
        """Persist a single job requirement and flush."""
        requirement = JobRequirement(
            application_id=application_id,
            text=text,
            category=category,
            priority=priority,
            req_metadata=req_metadata or {},
        )
        self.session.add(requirement)
        self.session.flush()
        return requirement

    def bulk_create(self, requirements: list[dict[str, Any]]) -> list[JobRequirement]:
        """Persist a batch of requirements from a list of attribute dicts."""
        objects = [JobRequirement(**req) for req in requirements]
        self.session.add_all(objects)
        self.session.flush()
        return objects

    def get(self, requirement_id: uuid.UUID) -> JobRequirement | None:
        """Return the requirement with *requirement_id*, or ``None``."""
        stmt = select(JobRequirement).where(JobRequirement.id == requirement_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_application(
        self, application_id: uuid.UUID
    ) -> Sequence[JobRequirement]:
        """Return all requirements for an application."""
        stmt = select(JobRequirement).where(
            JobRequirement.application_id == application_id
        )
        return self.session.execute(stmt).scalars().all()

    def update(
        self, requirement_id: uuid.UUID, **kwargs: Any
    ) -> JobRequirement | None:
        """Apply *kwargs* as attribute updates; return the updated object or ``None``."""
        requirement = self.get(requirement_id)
        if requirement is None:
            return None
        for key, value in kwargs.items():
            setattr(requirement, key, value)
        self.session.flush()
        return requirement

    def delete(self, requirement_id: uuid.UUID) -> bool:
        """Delete the requirement; return ``True`` if it existed."""
        requirement = self.get(requirement_id)
        if requirement is None:
            return False
        self.session.delete(requirement)
        self.session.flush()
        return True
