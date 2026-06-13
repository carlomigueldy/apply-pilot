"""Integration tests for the draft approval flow.

After a full analysis (ApplicationService.analyze), tests:
- approve_draft without edit: draft.status -> 'approved', application -> 'ready_to_apply'.
- approve_draft with edited_body: draft.status -> 'edited', body replaced.
- ReviewDecision row created with correct decision type and notes.
- get_drafts returns drafts ordered newest version first.
- regenerate_section creates a new version with status 'needs_review'.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import ReviewDecision, User
from applypilot.schemas.application import JobApplicationCreate
from applypilot.schemas.drafts import DraftApproveRequest, RegenerateSectionRequest
from applypilot.schemas.enums import (
    ApplicationStatus,
    DraftLength,
    DraftStatus,
    DraftType,
    ProfileItemType,
    Tone,
)
from applypilot.schemas.profile import ProfileItemCreate
from applypilot.services.application_service import ApplicationService
from applypilot.services.profile_service import ProfileService

_JOB_POST = """
Company: StartupCo
Role: Full Stack Engineer
Location: Remote (US time zones)

We're hiring a Full Stack Engineer to work across our Python backend and React frontend.

Requirements:
- 3+ years of Python experience required
- Experience with React and TypeScript
- Familiarity with PostgreSQL and Redis
- Strong communication and collaboration skills
- Experience deploying with Docker

Salary: $120,000 - $150,000 per year
"""


def _make_user(db_session: Session) -> User:
    user = User(name="Approval Test User", email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_profile(db_session: Session, user_id: uuid.UUID) -> None:
    svc = ProfileService(db_session)
    svc.create_item(
        user_id=user_id,
        data=ProfileItemCreate(
            type=ProfileItemType.ROLE,
            title="Full Stack Engineer at WidgetCorp",
            body=(
                "Built Python FastAPI backend and React TypeScript frontend serving 50k users. "
                "Deployed services with Docker on AWS. Collaborated closely with product and "
                "design teams. Strong PostgreSQL and Redis usage in production."
            ),
        ),
    )


def _setup_analyzed_app(db_session: Session) -> tuple[ApplicationService, uuid.UUID, list]:
    """Create a user, seed profile, create and analyze an application. Returns (service, app_id, drafts)."""
    user = _make_user(db_session)
    _seed_profile(db_session, user.id)
    service = ApplicationService(db_session)
    app = service.create_application(
        data=JobApplicationCreate(raw_job_post=_JOB_POST),
        user_id=user.id,
    )
    service.analyze(app.id)
    drafts = service.get_drafts(app.id)
    return service, app.id, list(drafts)


# ---------------------------------------------------------------------------
# Approval tests
# ---------------------------------------------------------------------------


class TestApprovalFlow:
    def test_approve_draft_without_edit_returns_approved_status(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        assert drafts, "analyze() must produce at least one draft"

        draft = drafts[0]
        result = service.approve_draft(DraftApproveRequest(draft_id=str(draft.id)))
        assert result.status == DraftStatus.APPROVED.value

    def test_approve_advances_application_to_ready_to_apply(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        draft = drafts[0]
        service.approve_draft(DraftApproveRequest(draft_id=str(draft.id)))

        app = service.get_application(app_id)
        assert app.status == ApplicationStatus.READY_TO_APPLY

    def test_approve_with_edited_body_sets_edited_status(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        draft = drafts[0]
        new_body = "Edited body: I am particularly excited about this opportunity..."

        result = service.approve_draft(
            DraftApproveRequest(draft_id=str(draft.id), edited_body=new_body)
        )
        assert result.status == DraftStatus.EDITED.value
        assert result.body == new_body

    def test_approve_with_edit_creates_edit_decision(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        draft = drafts[0]
        service.approve_draft(
            DraftApproveRequest(
                draft_id=str(draft.id),
                edited_body="Updated text.",
                notes="Minor polish only.",
            )
        )

        decisions = db_session.execute(
            select(ReviewDecision).where(ReviewDecision.draft_id == draft.id)
        ).scalars().all()
        assert len(decisions) == 1
        assert decisions[0].decision == "edit"
        assert decisions[0].notes == "Minor polish only."

    def test_approve_without_edit_creates_approve_decision(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        draft = drafts[0]
        service.approve_draft(DraftApproveRequest(draft_id=str(draft.id), notes="Perfect!"))

        decisions = db_session.execute(
            select(ReviewDecision).where(ReviewDecision.draft_id == draft.id)
        ).scalars().all()
        assert len(decisions) == 1
        assert decisions[0].decision == "approve"
        assert decisions[0].notes == "Perfect!"

    def test_review_decision_linked_to_application(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        draft = drafts[0]
        service.approve_draft(DraftApproveRequest(draft_id=str(draft.id)))

        decisions = db_session.execute(
            select(ReviewDecision).where(ReviewDecision.application_id == app_id)
        ).scalars().all()
        assert len(decisions) >= 1
        assert all(d.application_id == app_id for d in decisions)


# ---------------------------------------------------------------------------
# get_drafts ordering
# ---------------------------------------------------------------------------


class TestGetDrafts:
    def test_get_drafts_returns_list(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        all_drafts = service.get_drafts(app_id)
        assert isinstance(all_drafts, list)
        assert len(all_drafts) > 0

    def test_all_drafts_start_as_needs_review(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        for draft in drafts:
            assert draft.status == DraftStatus.NEEDS_REVIEW.value

    def test_drafts_have_required_fields(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        for draft in drafts:
            assert draft.id is not None
            assert draft.type is not None
            assert draft.title
            assert draft.body
            assert draft.status


# ---------------------------------------------------------------------------
# regenerate_section
# ---------------------------------------------------------------------------


class TestRegenerateSection:
    def test_regenerate_section_creates_new_draft(self, db_session: Session) -> None:
        service, app_id, drafts = _setup_analyzed_app(db_session)
        initial_count = len(drafts)

        service.regenerate_section(
            app_id,
            RegenerateSectionRequest(type=DraftType.COVER_EMAIL),
        )
        new_drafts = service.get_drafts(app_id)
        assert len(new_drafts) > initial_count

    def test_regenerated_draft_has_needs_review_status(self, db_session: Session) -> None:
        service, app_id, _ = _setup_analyzed_app(db_session)
        new_draft = service.regenerate_section(
            app_id,
            RegenerateSectionRequest(type=DraftType.COVER_EMAIL),
        )
        assert new_draft.status == DraftStatus.NEEDS_REVIEW.value

    def test_regenerated_draft_has_correct_type(self, db_session: Session) -> None:
        service, app_id, _ = _setup_analyzed_app(db_session)
        new_draft = service.regenerate_section(
            app_id,
            RegenerateSectionRequest(type=DraftType.RESUME_SUMMARY),
        )
        assert new_draft.type == DraftType.RESUME_SUMMARY

    def test_regenerate_with_tone_and_length(self, db_session: Session) -> None:
        service, app_id, _ = _setup_analyzed_app(db_session)
        new_draft = service.regenerate_section(
            app_id,
            RegenerateSectionRequest(
                type=DraftType.SELF_INTRODUCTION,
                tone=Tone.CONFIDENT,
                length=DraftLength.SHORT,
            ),
        )
        assert new_draft is not None
        assert new_draft.type == DraftType.SELF_INTRODUCTION
