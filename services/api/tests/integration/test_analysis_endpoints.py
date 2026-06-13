"""Integration tests for the job-application HTTP endpoints.

Tests via FastAPI TestClient (client fixture from conftest.py):
- POST /api/applications -> 201 with JobApplicationRead shape.
- POST /api/applications/{id}/analyze -> 200 with AnalyzeResponse shape.
- GET /api/applications/{id}/analysis -> 200 with FitAnalysis shape.
- GET /api/applications/{id}/evidence -> 200 (list).
- GET /api/applications/{id}/drafts -> 200 with DraftRead items having status 'needs_review'.
- POST /api/applications/{id}/approve-draft -> 200, draft status 'approved'.
- GET /api/applications/{id} -> 200, application status 'drafted' after analyze.
- 404 responses for unknown IDs.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from applypilot.db.models import User
from applypilot.schemas.enums import (
    ApplicationStatus,
    DraftStatus,
    GraphRunStatus,
    ProfileItemType,
)
from applypilot.schemas.profile import ProfileItemCreate
from applypilot.services.profile_service import ProfileService

_JOB_POST = """
Company: GlobalTech
Role: Backend Python Developer
Location: Hybrid (US)

We are seeking a Backend Python Developer to join our engineering team.

Key Requirements:
- 3+ years Python experience required
- FastAPI or Django REST Framework
- PostgreSQL database experience
- Experience with Docker and containerisation
- Strong REST API design skills must have
- Bonus: experience with LangChain or OpenAI integrations

Compensation: $110,000 - $140,000 per year
Remote-friendly, primarily EST hours
"""


def _make_user(db_session: Session) -> User:
    user = User(name="Endpoint Test User", email=f"{uuid.uuid4()}@test.com")
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
            title="Python Backend Developer at WebApp Inc",
            body=(
                "Built and maintained FastAPI services for a SaaS platform. "
                "Designed PostgreSQL schemas for high-traffic tables. "
                "Containerised services with Docker and Docker Compose. "
                "Integrated OpenAI APIs for document processing features. "
                "Wrote unit and integration tests achieving 85% coverage."
            ),
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/applications
# ---------------------------------------------------------------------------


class TestCreateApplicationEndpoint:
    def test_create_application_returns_201(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        response = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        assert response.status_code == 201

    def test_create_application_response_shape(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        response = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["status"] == ApplicationStatus.SAVED.value

    def test_create_application_too_short_returns_422(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        response = client.post(
            "/api/applications",
            json={"raw_job_post": "Too short"},
            params={"user_id": str(user.id)},
        )
        assert response.status_code == 422

    def test_create_application_missing_raw_job_post_returns_422(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        response = client.post(
            "/api/applications",
            json={},
            params={"user_id": str(user.id)},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/applications/{id}
# ---------------------------------------------------------------------------


class TestGetApplicationEndpoint:
    def test_get_application_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]

        response = client.get(f"/api/applications/{app_id}")
        assert response.status_code == 200

    def test_get_unknown_application_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.get(f"/api/applications/{uuid.uuid4()}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/applications/{id}/analyze
# ---------------------------------------------------------------------------


class TestAnalyzeEndpoint:
    def test_analyze_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]

        response = client.post(f"/api/applications/{app_id}/analyze")
        assert response.status_code == 200

    def test_analyze_response_shape(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]

        response = client.post(f"/api/applications/{app_id}/analyze")
        data = response.json()
        assert "application_id" in data
        assert "graph_run_id" in data
        assert "status" in data
        assert data["status"] == GraphRunStatus.COMPLETED.value

    def test_analyze_unknown_application_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        response = client.post(f"/api/applications/{uuid.uuid4()}/analyze")
        assert response.status_code == 404

    def test_application_status_is_drafted_after_analyze(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")

        get_resp = client.get(f"/api/applications/{app_id}")
        assert get_resp.json()["status"] == ApplicationStatus.DRAFTED.value


# ---------------------------------------------------------------------------
# GET /api/applications/{id}/analysis
# ---------------------------------------------------------------------------


class TestGetAnalysisEndpoint:
    def _analyze(self, client: TestClient, db_session: Session) -> str:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")
        return app_id

    def test_get_analysis_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._analyze(client, db_session)
        response = client.get(f"/api/applications/{app_id}/analysis")
        assert response.status_code == 200

    def test_get_analysis_response_shape(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._analyze(client, db_session)
        response = client.get(f"/api/applications/{app_id}/analysis")
        data = response.json()
        assert "fit_score" in data
        assert "summary" in data
        assert "items" in data
        assert "red_flags" in data
        assert "positioning_strategy" in data
        assert 0 <= data["fit_score"] <= 100

    def test_get_analysis_items_is_list(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._analyze(client, db_session)
        response = client.get(f"/api/applications/{app_id}/analysis")
        data = response.json()
        assert isinstance(data["items"], list)

    def test_get_analysis_without_analyze_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        response = client.get(f"/api/applications/{app_id}/analysis")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/applications/{id}/evidence
# ---------------------------------------------------------------------------


class TestGetEvidenceEndpoint:
    def test_get_evidence_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")

        response = client.get(f"/api/applications/{app_id}/evidence")
        assert response.status_code == 200

    def test_get_evidence_returns_list(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")

        response = client.get(f"/api/applications/{app_id}/evidence")
        assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# GET /api/applications/{id}/drafts
# ---------------------------------------------------------------------------


class TestGetDraftsEndpoint:
    def _setup(self, client: TestClient, db_session: Session) -> str:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")
        return app_id

    def test_get_drafts_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._setup(client, db_session)
        response = client.get(f"/api/applications/{app_id}/drafts")
        assert response.status_code == 200

    def test_get_drafts_returns_list_with_items(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._setup(client, db_session)
        response = client.get(f"/api/applications/{app_id}/drafts")
        drafts = response.json()
        assert isinstance(drafts, list)
        assert len(drafts) > 0

    def test_drafts_have_needs_review_status(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._setup(client, db_session)
        response = client.get(f"/api/applications/{app_id}/drafts")
        drafts = response.json()
        for draft in drafts:
            assert draft["status"] == DraftStatus.NEEDS_REVIEW.value

    def test_draft_has_required_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id = self._setup(client, db_session)
        response = client.get(f"/api/applications/{app_id}/drafts")
        drafts = response.json()
        assert len(drafts) > 0
        required_fields = {"id", "application_id", "type", "title", "body", "status", "version"}
        for draft in drafts:
            missing = required_fields - draft.keys()
            assert not missing, f"Draft missing fields: {missing}"


# ---------------------------------------------------------------------------
# POST /api/applications/{id}/approve-draft
# ---------------------------------------------------------------------------


class TestApproveDraftEndpoint:
    def _setup_with_draft(self, client: TestClient, db_session: Session) -> tuple[str, str]:
        """Returns (app_id, draft_id)."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]
        client.post(f"/api/applications/{app_id}/analyze")

        drafts_resp = client.get(f"/api/applications/{app_id}/drafts")
        drafts = drafts_resp.json()
        draft_id = drafts[0]["id"]
        return app_id, draft_id

    def test_approve_draft_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id, draft_id = self._setup_with_draft(client, db_session)
        response = client.post(
            f"/api/applications/{app_id}/approve-draft",
            json={"draft_id": draft_id},
        )
        assert response.status_code == 200

    def test_approve_draft_flips_status_to_approved(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id, draft_id = self._setup_with_draft(client, db_session)
        response = client.post(
            f"/api/applications/{app_id}/approve-draft",
            json={"draft_id": draft_id},
        )
        data = response.json()
        assert data["status"] == DraftStatus.APPROVED.value

    def test_approve_draft_with_edit_sets_edited_status(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id, draft_id = self._setup_with_draft(client, db_session)
        response = client.post(
            f"/api/applications/{app_id}/approve-draft",
            json={"draft_id": draft_id, "edited_body": "My custom edited cover letter."},
        )
        data = response.json()
        assert data["status"] == DraftStatus.EDITED.value
        assert data["body"] == "My custom edited cover letter."

    def test_approve_draft_advances_application_to_ready_to_apply(
        self, client: TestClient, db_session: Session
    ) -> None:
        app_id, draft_id = self._setup_with_draft(client, db_session)
        client.post(
            f"/api/applications/{app_id}/approve-draft",
            json={"draft_id": draft_id},
        )

        get_resp = client.get(f"/api/applications/{app_id}")
        assert get_resp.json()["status"] == ApplicationStatus.READY_TO_APPLY.value

    def test_approve_non_existent_draft_returns_404(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        create_resp = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        app_id = create_resp.json()["id"]

        response = client.post(
            f"/api/applications/{app_id}/approve-draft",
            json={"draft_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/applications  (list)
# ---------------------------------------------------------------------------


class TestListApplicationsEndpoint:
    def test_list_without_user_id_returns_200(self, client: TestClient) -> None:
        """The web UI sends no user_id; the list must default to the demo user.

        Regression guard: this endpoint previously required ``user_id`` and 422'd
        for every dashboard/list load.
        """
        response = client.get("/api/applications")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_with_explicit_user_id_returns_200(
        self, client: TestClient, db_session: Session
    ) -> None:
        user = _make_user(db_session)
        create = client.post(
            "/api/applications",
            json={"raw_job_post": _JOB_POST},
            params={"user_id": str(user.id)},
        )
        assert create.status_code == 201
        response = client.get("/api/applications", params={"user_id": str(user.id)})
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()}
        assert create.json()["id"] in ids
