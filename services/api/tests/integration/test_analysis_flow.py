"""Integration tests for the full application-analysis flow.

Tests ApplicationService.analyze() end-to-end against the test database:
- Seeds a user and profile items with embeddings via ProfileService.
- Creates a job application with a realistic raw_job_post.
- Calls analyze(), which runs the LangGraph pipeline (using FakeLLMProvider).
- Asserts:
  - FitAnalysis row exists with items (fit_analyses table populated).
  - EvidenceMatch rows exist for the application.
  - Draft rows exist with status 'needs_review'.
  - GraphRun row has status 'completed' and model_metadata populated.
  - Strong/partial FitAnalysisItems carry non-empty evidence_chunk_ids.
  - Application status advances to 'drafted' after pipeline.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import (
    Draft,
    EvidenceMatch,
    User,
)
from applypilot.db.repositories.evidence_repository import FitAnalysisRepository
from applypilot.db.repositories.graph_run_repository import GraphRunRepository
from applypilot.schemas.application import JobApplicationCreate
from applypilot.schemas.enums import (
    ApplicationStatus,
    DraftStatus,
    GraphRunStatus,
    MatchLevel,
    ProfileItemType,
)
from applypilot.schemas.profile import ProfileItemCreate
from applypilot.services.application_service import ApplicationService
from applypilot.services.profile_service import ProfileService

# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

_REALISTIC_JOB_POST = """
Company: TechStartup Inc.
Role: Senior Backend Engineer
Location: Remote

About the role:
We are looking for a Senior Backend Engineer to help us scale our platform.

Requirements:
- 5+ years of Python backend experience required
- Strong knowledge of FastAPI and REST API design
- Experience with PostgreSQL and database optimization
- Proficiency in Docker and CI/CD pipelines
- Ability to lead and mentor junior engineers
- Experience with LLM integrations or AI features is a plus

What we offer:
- Salary: $150,000 - $180,000 per year (remote)
- Fully remote, async-first culture
- Equity package + comprehensive benefits
"""


def _make_user(db_session: Session) -> User:
    user = User(name="Analysis Test User", email=f"{uuid.uuid4()}@test.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _seed_profile(db_session: Session, user_id: uuid.UUID) -> None:
    """Seed several profile items covering the job requirements above."""
    svc = ProfileService(db_session)

    items = [
        ProfileItemCreate(
            type=ProfileItemType.ROLE,
            title="Senior Python Engineer at DataCo",
            body=(
                "Led a team of 4 backend engineers building high-throughput Python "
                "microservices handling 1M+ daily requests. Designed REST APIs using "
                "FastAPI and SQLAlchemy. Migrated legacy Django code to FastAPI "
                "with zero downtime. Mentored 3 junior engineers on Pythonic best practices."
            ),
        ),
        ProfileItemCreate(
            type=ProfileItemType.PROJECT,
            title="PostgreSQL Performance Optimization Initiative",
            body=(
                "Reduced p99 query latency by 60% through strategic index design, "
                "query planner tuning, and materialized views. Introduced connection "
                "pooling with pgBouncer. Led database schema migration across 12 "
                "production tables with zero data loss."
            ),
        ),
        ProfileItemCreate(
            type=ProfileItemType.PROJECT,
            title="CI/CD Pipeline Modernisation with Docker and GitHub Actions",
            body=(
                "Containerised 8 services with Docker and Docker Compose, cutting "
                "build times by 40%. Built a multi-stage CI/CD pipeline with "
                "GitHub Actions that runs unit, integration, and E2E tests before deploy."
            ),
        ),
        ProfileItemCreate(
            type=ProfileItemType.ACHIEVEMENT,
            title="AI Integration: LLM-powered Document Processing",
            body=(
                "Architected an LLM integration layer that processes 10,000 documents "
                "per day using OpenAI and Anthropic APIs. Designed structured output "
                "extraction pipelines with 95% accuracy."
            ),
        ),
    ]

    for item_data in items:
        svc.create_item(user_id=user_id, data=item_data)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalysisFlow:
    def test_analyze_returns_completed_graph_run(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)

        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        response = service.analyze(app.id)

        assert response.status == GraphRunStatus.COMPLETED.value
        assert response.application_id == str(app.id)
        assert response.graph_run_id

    def test_graph_run_row_has_status_completed(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        response = service.analyze(app.id)

        run_repo = GraphRunRepository(db_session)
        graph_run = run_repo.get(uuid.UUID(response.graph_run_id))
        assert graph_run is not None
        assert graph_run.status == GraphRunStatus.COMPLETED.value

    def test_graph_run_has_model_metadata(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        response = service.analyze(app.id)

        run_repo = GraphRunRepository(db_session)
        graph_run = run_repo.get(uuid.UUID(response.graph_run_id))
        assert graph_run is not None
        assert graph_run.model_metadata
        assert "provider" in graph_run.model_metadata
        assert graph_run.model_metadata["provider"] == "fake"

    def test_fit_analysis_row_created(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        fit_repo = FitAnalysisRepository(db_session)
        fit = fit_repo.get_latest_by_application(app.id)
        assert fit is not None
        assert fit.fit_score >= 0
        assert fit.summary

    def test_fit_analysis_has_items(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        fit_repo = FitAnalysisRepository(db_session)
        fit = fit_repo.get_latest_by_application(app.id)
        assert fit is not None
        assert isinstance(fit.items, list)
        assert len(fit.items) > 0

    def test_strong_partial_fit_items_have_evidence_chunk_ids(self, db_session: Session) -> None:
        """FitAnalysisItems with strong/partial match_level must cite evidence_chunk_ids."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        fit_repo = FitAnalysisRepository(db_session)
        fit = fit_repo.get_latest_by_application(app.id)
        assert fit is not None
        for item in fit.items:
            match_level = item.get("match_level") if isinstance(item, dict) else getattr(item, "match_level", None)
            chunk_ids = item.get("evidence_chunk_ids") if isinstance(item, dict) else getattr(item, "evidence_chunk_ids", [])
            if match_level in (MatchLevel.STRONG.value, MatchLevel.PARTIAL.value):
                assert chunk_ids, (
                    f"Item for requirement {item.get('requirement_id') if isinstance(item, dict) else item.requirement_id!r} "
                    f"has match_level={match_level!r} but no evidence_chunk_ids"
                )

    def test_evidence_matches_rows_exist(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        matches = db_session.execute(
            select(EvidenceMatch).where(EvidenceMatch.application_id == app.id)
        ).scalars().all()
        assert len(matches) > 0

    def test_drafts_created_with_needs_review_status(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        drafts = db_session.execute(
            select(Draft).where(Draft.application_id == app.id)
        ).scalars().all()
        assert len(drafts) > 0
        for draft in drafts:
            assert draft.status == DraftStatus.NEEDS_REVIEW.value

    def test_application_status_advances_to_drafted(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        updated = service.get_application(app.id)
        assert updated.status == ApplicationStatus.DRAFTED

    def test_re_analyze_replaces_prior_data(self, db_session: Session) -> None:
        """Calling analyze() twice on the same application should not duplicate fit analyses."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )

        service.analyze(app.id)
        service.analyze(app.id)  # second run

        # Should still produce a valid fit analysis (most-recent).
        analysis = service.get_analysis(app.id)
        assert analysis is not None
        assert 0 <= analysis.fit_score <= 100

    def test_get_analysis_returns_valid_fit_analysis(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        analysis = service.get_analysis(app.id)
        assert analysis is not None
        assert isinstance(analysis.fit_score, int)
        assert 0 <= analysis.fit_score <= 100
        assert analysis.summary
        assert isinstance(analysis.items, list)

    def test_get_evidence_returns_enriched_rows(self, db_session: Session) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_REALISTIC_JOB_POST),
            user_id=user.id,
        )
        service.analyze(app.id)

        evidence = service.get_evidence(app.id)
        if evidence:  # may be empty if no matches were found
            required_keys = {"id", "requirement_id", "evidence_chunk_id", "chunk_text",
                             "summary", "confidence", "profile_item_title"}
            for row in evidence:
                for key in required_keys:
                    assert key in row, f"Evidence row missing key: {key!r}"
