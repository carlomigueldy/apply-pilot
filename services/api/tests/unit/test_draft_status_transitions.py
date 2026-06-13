"""Unit tests for draft status transitions and approval logic.

Tests the DraftRepository status helpers and ApplicationService.approve_draft
using a live test database session (db_session fixture from conftest.py).

Covers:
- set_status transitions: generated -> approved, needs_review -> edited, etc.
- approve_draft without edit -> status 'approved', review_decision created.
- approve_draft with edited_body -> status 'edited', body replaced.
- First approval advances application to 'ready_to_apply'.
- Second approval does NOT re-advance (already ready_to_apply).
- approve_draft raises ValueError for a non-existent draft id.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from applypilot.db.models import Draft, ReviewDecision, User
from applypilot.db.repositories.draft_repository import DraftRepository
from applypilot.schemas.application import JobApplicationCreate
from applypilot.schemas.drafts import DraftApproveRequest
from applypilot.schemas.enums import ApplicationStatus, DraftStatus, DraftType
from applypilot.services.application_service import ApplicationService

# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _make_user(db_session: Session) -> User:
    user = User(name="Draft Test User", email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _make_application(service: ApplicationService, user_id: uuid.UUID) -> uuid.UUID:
    app = service.create_application(
        data=JobApplicationCreate(
            raw_job_post=(
                "Senior Python Engineer at AcmeCorp. "
                "We need someone with 5+ years of Python experience, "
                "strong REST API skills, and team leadership abilities."
            )
        ),
        user_id=user_id,
    )
    return app.id


def _make_draft(
    db_session: Session,
    application_id: uuid.UUID,
    status: str = DraftStatus.NEEDS_REVIEW.value,
    draft_type: str = DraftType.COVER_EMAIL.value,
) -> Draft:
    repo = DraftRepository(db_session)
    draft = repo.create(
        application_id=application_id,
        type=draft_type,
        title="Cover Letter",
        body="Dear Hiring Manager, I am excited to apply...",
        status=status,
    )
    db_session.commit()
    return draft


# ---------------------------------------------------------------------------
# DraftRepository.set_status transitions
# ---------------------------------------------------------------------------


class TestDraftStatusTransitions:
    def test_set_status_needs_review_to_approved(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id, status=DraftStatus.NEEDS_REVIEW.value)

        repo = DraftRepository(db_session)
        updated = repo.set_status(draft.id, DraftStatus.APPROVED.value)
        assert updated is not None
        assert updated.status == DraftStatus.APPROVED.value

    def test_set_status_generated_to_needs_review(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id, status=DraftStatus.GENERATED.value)

        repo = DraftRepository(db_session)
        updated = repo.set_status(draft.id, DraftStatus.NEEDS_REVIEW.value)
        assert updated is not None
        assert updated.status == DraftStatus.NEEDS_REVIEW.value

    def test_set_status_returns_none_for_missing_draft(self, db_session: Session) -> None:
        repo = DraftRepository(db_session)
        result = repo.set_status(uuid.uuid4(), DraftStatus.APPROVED.value)
        assert result is None

    def test_draft_update_replaces_body(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        repo = DraftRepository(db_session)
        new_body = "Updated cover letter body with more details."
        updated = repo.update(draft.id, body=new_body, status=DraftStatus.EDITED.value)
        assert updated is not None
        assert updated.body == new_body
        assert updated.status == DraftStatus.EDITED.value

    def test_set_status_to_rejected(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        repo = DraftRepository(db_session)
        updated = repo.set_status(draft.id, DraftStatus.REJECTED.value)
        assert updated is not None
        assert updated.status == DraftStatus.REJECTED.value


# ---------------------------------------------------------------------------
# ApplicationService.approve_draft
# ---------------------------------------------------------------------------


class TestApproveDraft:
    def test_approve_without_edit_sets_status_approved(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        result = service.approve_draft(DraftApproveRequest(draft_id=str(draft.id)))
        assert result.status == DraftStatus.APPROVED.value

    def test_approve_with_edited_body_sets_status_edited(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)
        new_body = "Edited cover letter: I am particularly excited about..."

        result = service.approve_draft(
            DraftApproveRequest(draft_id=str(draft.id), edited_body=new_body)
        )
        assert result.status == DraftStatus.EDITED.value
        assert result.body == new_body

    def test_first_approval_advances_application_to_ready_to_apply(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        service.approve_draft(DraftApproveRequest(draft_id=str(draft.id)))

        updated_app = service.get_application(app_id)
        assert updated_app.status == ApplicationStatus.READY_TO_APPLY

    def test_review_decision_created_on_approval(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        service.approve_draft(DraftApproveRequest(draft_id=str(draft.id), notes="Looks great!"))

        decisions = db_session.query(ReviewDecision).filter_by(draft_id=draft.id).all()
        assert len(decisions) == 1
        assert decisions[0].decision == "approve"
        assert decisions[0].notes == "Looks great!"

    def test_review_decision_type_edit_when_body_provided(self, db_session: Session) -> None:
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)
        draft = _make_draft(db_session, app_id)

        service.approve_draft(
            DraftApproveRequest(draft_id=str(draft.id), edited_body="Updated body.")
        )

        decisions = db_session.query(ReviewDecision).filter_by(draft_id=draft.id).all()
        assert len(decisions) == 1
        assert decisions[0].decision == "edit"

    def test_second_approval_does_not_revert_application_status(self, db_session: Session) -> None:
        """After the first approval advances to ready_to_apply, a second remains unchanged."""
        user = _make_user(db_session)
        service = ApplicationService(db_session)
        app_id = _make_application(service, user.id)

        draft1 = _make_draft(db_session, app_id, draft_type=DraftType.COVER_EMAIL.value)
        draft2 = _make_draft(db_session, app_id, draft_type=DraftType.RECRUITER_REPLY.value)

        service.approve_draft(DraftApproveRequest(draft_id=str(draft1.id)))
        service.approve_draft(DraftApproveRequest(draft_id=str(draft2.id)))

        updated_app = service.get_application(app_id)
        assert updated_app.status == ApplicationStatus.READY_TO_APPLY

    def test_approve_non_existent_draft_raises_value_error(self, db_session: Session) -> None:
        service = ApplicationService(db_session)
        with pytest.raises(ValueError, match="not found"):
            service.approve_draft(DraftApproveRequest(draft_id=str(uuid.uuid4())))
