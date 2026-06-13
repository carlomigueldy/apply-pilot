"""Schemas for extracted job details and job requirements."""

from __future__ import annotations

from pydantic import BaseModel

from applypilot.schemas.enums import (
    RequirementCategory,
    RequirementPriority,
    WorkArrangement,
)


class ExtractedJob(BaseModel):
    """Structured details extracted from a raw job post."""

    company_name: str | None = None
    role_title: str | None = None
    work_arrangement: WorkArrangement = WorkArrangement.UNKNOWN
    salary_text: str | None = None
    timezone_text: str | None = None
    location: str | None = None
    summary: str


class JobRequirement(BaseModel):
    """A single requirement extracted from a job post."""

    id: str
    text: str
    category: RequirementCategory
    priority: RequirementPriority


class JobRequirementList(BaseModel):
    """Structured list of extracted job requirements."""

    requirements: list[JobRequirement]
