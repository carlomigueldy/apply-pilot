"""Schemas for job applications and analysis triggering."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from applypilot.schemas.common import ORMModel, TimestampedSchema
from applypilot.schemas.enums import ApplicationStatus, WorkArrangement


class JobApplicationCreate(BaseModel):
    """Payload to create a job application from a raw job post."""

    raw_job_post: str = Field(min_length=30)
    company_name: str | None = None
    role_title: str | None = None
    job_url: str | None = None
    salary_text: str | None = None
    work_arrangement: WorkArrangement | None = None
    timezone_text: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None


class JobApplicationUpdate(BaseModel):
    """Payload to partially update a job application; all fields optional."""

    company_name: str | None = None
    role_title: str | None = None
    job_url: str | None = None
    raw_job_post: str | None = None
    status: ApplicationStatus | None = None
    work_arrangement: WorkArrangement | None = None
    salary_text: str | None = None
    timezone_text: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None


class JobApplicationRead(ORMModel, TimestampedSchema):
    """A job application as returned from the API."""

    id: UUID
    user_id: UUID
    company_name: str | None = None
    role_title: str | None = None
    job_url: str | None = None
    raw_job_post: str | None = None
    status: ApplicationStatus
    work_arrangement: WorkArrangement | None = None
    salary_text: str | None = None
    timezone_text: str | None = None
    recruiter_name: str | None = None
    recruiter_email: str | None = None


class ApplicationListItem(ORMModel):
    """Condensed job application for list views."""

    id: UUID
    company_name: str | None = None
    role_title: str | None = None
    status: ApplicationStatus
    fit_score: int | None = None
    created_at: datetime
    updated_at: datetime


class AnalyzeResponse(BaseModel):
    """Response returned when an analysis graph run is started."""

    application_id: str
    graph_run_id: str
    status: str
