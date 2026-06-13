"""Application routes — full job-application lifecycle API.

Exposes CRUD, AI analysis, draft generation, approval, and section-regeneration
endpoints under the ``/applications`` prefix.  All handlers are **synchronous**
(plain ``def``).
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from applypilot.api.deps import SessionDep
from applypilot.schemas.application import (
    AnalyzeResponse,
    ApplicationListItem,
    JobApplicationCreate,
    JobApplicationRead,
    JobApplicationUpdate,
)
from applypilot.schemas.drafts import DraftApproveRequest, DraftRead, RegenerateSectionRequest
from applypilot.schemas.fit import FitAnalysis
from applypilot.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])

# Seeded demo user — used as default owner when no user_id is supplied (local dev / smoke tests).
_DEMO_USER_ID = uuid.UUID("a0000000-0000-4000-8000-000000000001")

# Annotated query-param aliases for concise handler signatures.
# user_id is optional everywhere; omitting it falls back to the demo seed user
# (ApplyPilot is a single-user local app, so the web UI never sends one).
OptionalUserIdQuery = Annotated[
    uuid.UUID,
    Query(description="Owner user ID (defaults to demo seed user when omitted)"),
]
OptionalApplicationIdQuery = Annotated[
    uuid.UUID | None,
    Query(alias="application_id", description="Filter by application ID"),
]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    session: SessionDep,
    user_id: OptionalUserIdQuery = _DEMO_USER_ID,
) -> list[ApplicationListItem]:
    """List job applications, newest first, with latest fit score.

    ``user_id`` is optional; omitting it lists the seeded demo user's applications.
    ApplyPilot is a single-user local app, so the web UI never sends one.
    """
    return ApplicationService(session).list_applications(user_id=user_id)


@router.post("", response_model=JobApplicationRead, status_code=201)
def create_application(
    data: JobApplicationCreate,
    session: SessionDep,
    user_id: OptionalUserIdQuery = _DEMO_USER_ID,
) -> JobApplicationRead:
    """Create a new job application from a raw job post (status: ``saved``).

    ``user_id`` is optional; when omitted the seeded demo user is used, which is
    convenient for local development and smoke tests.
    """
    return ApplicationService(session).create_application(data=data, user_id=user_id)


@router.get("/{application_id}", response_model=JobApplicationRead)
def get_application(
    application_id: uuid.UUID,
    session: SessionDep,
) -> JobApplicationRead:
    """Retrieve a single job application by ID."""
    try:
        return ApplicationService(session).get_application(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{application_id}", response_model=JobApplicationRead)
def update_application(
    application_id: uuid.UUID,
    data: JobApplicationUpdate,
    session: SessionDep,
) -> JobApplicationRead:
    """Partially update a job application."""
    try:
        return ApplicationService(session).update_application(application_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


@router.post("/{application_id}/analyze", response_model=AnalyzeResponse)
def analyze_application(
    application_id: uuid.UUID,
    session: SessionDep,
) -> AnalyzeResponse:
    """Run (or re-run) the full AI analysis pipeline for a job application.

    Clears prior requirements, evidence matches, and fit analyses before
    triggering the LangGraph pipeline.
    """
    try:
        return ApplicationService(session).analyze(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{application_id}/analysis", response_model=FitAnalysis)
def get_analysis(
    application_id: uuid.UUID,
    session: SessionDep,
) -> FitAnalysis:
    """Retrieve the latest fit analysis for a job application."""
    try:
        return ApplicationService(session).get_analysis(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{application_id}/evidence", response_model=list[dict[str, Any]])
def get_evidence(
    application_id: uuid.UUID,
    session: SessionDep,
) -> list[dict[str, Any]]:
    """Return evidence matches for a job application, joined with chunk and title data."""
    return ApplicationService(session).get_evidence(application_id)


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------


@router.get("/{application_id}/drafts", response_model=list[DraftRead])
def get_drafts(
    application_id: uuid.UUID,
    session: SessionDep,
) -> list[DraftRead]:
    """List all generated drafts for a job application, newest version first."""
    return ApplicationService(session).get_drafts(application_id)


@router.post("/{application_id}/generate-drafts", response_model=list[DraftRead])
def generate_drafts(
    application_id: uuid.UUID,
    session: SessionDep,
) -> list[DraftRead]:
    """Regenerate the full draft bundle as new versioned rows (status: ``needs_review``)."""
    try:
        return ApplicationService(session).generate_drafts(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{application_id}/approve-draft", response_model=DraftRead)
def approve_draft(
    application_id: uuid.UUID,  # noqa: ARG001 — validated by path; draft FK owns scope
    data: DraftApproveRequest,
    session: SessionDep,
) -> DraftRead:
    """Approve (and optionally edit) a draft, recording the review decision.

    When ``edited_body`` is provided the draft body is replaced and the status
    is set to ``edited``; otherwise the status is set to ``approved``.  On the
    first approval/edit for the application, the application advances to
    ``ready_to_apply``.
    """
    try:
        return ApplicationService(session).approve_draft(data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{application_id}/regenerate-section", response_model=DraftRead)
def regenerate_section(
    application_id: uuid.UUID,
    data: RegenerateSectionRequest,
    session: SessionDep,
) -> DraftRead:
    """Regenerate a single draft section as a new versioned row.

    Accepts optional ``tone``, ``length``, and free-form ``instructions`` to
    guide the regeneration.
    """
    try:
        return ApplicationService(session).regenerate_section(application_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
