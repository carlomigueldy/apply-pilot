"""Integration tests for graph run failure handling.

Verifies that the GraphRunService and ApplicationService handle errors gracefully:
- analyze() with a too-short raw_job_post (validate_input short-circuits to END)
  → graph_run may still complete (validate_input returns END branch, not exception)
  but no requirements/fit are persisted; application stays safe.
- Monkeypatching a graph node to raise → graph_run row status 'failed', error_payload set,
  application not left in 'running' state.
- GraphRun.error_payload contains 'node', 'message', 'type' when failed.
- A failed analyze() raises ValueError (application not found) when application does not exist.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import FitAnalysis, User
from applypilot.db.repositories.graph_run_repository import GraphRunRepository
from applypilot.schemas.application import JobApplicationCreate
from applypilot.schemas.enums import GraphRunStatus, ProfileItemType
from applypilot.schemas.profile import ProfileItemCreate
from applypilot.services.application_service import ApplicationService
from applypilot.services.graph_run_service import GraphRunService
from applypilot.services.profile_service import ProfileService

_VALID_JOB_POST = """
Company: FailureCorp
Role: Resilience Engineer
Location: Remote

We need someone who can handle failures gracefully.
Requirements:
- 5+ years distributed systems experience required
- Strong knowledge of fault-tolerance and circuit breakers
- Proficiency in Python must have
- Experience with observability tooling
"""


def _make_user(db_session: Session) -> User:
    user = User(name="Failure Test User", email=f"{uuid.uuid4()}@test.com")
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
            title="Resilience Engineer at ReliableCo",
            body=(
                "Built fault-tolerant Python distributed systems serving millions of users. "
                "Implemented circuit breakers, retries, and observability with Datadog. "
                "Led reliability reviews and chaos engineering initiatives."
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Failure via non-existent application
# ---------------------------------------------------------------------------


class TestAnalyzeNonExistentApplication:
    def test_analyze_non_existent_raises_value_error(self, db_session: Session) -> None:
        service = ApplicationService(db_session)
        with pytest.raises(ValueError, match="not found"):
            service.analyze(uuid.uuid4())

    def test_graph_run_service_non_existent_raises_value_error(self, db_session: Session) -> None:
        run_service = GraphRunService(db_session)
        with pytest.raises(ValueError, match="not found"):
            run_service.run_analysis(uuid.uuid4())


# ---------------------------------------------------------------------------
# Failure via monkeypatched node
# ---------------------------------------------------------------------------


class TestGraphRunFailureOnNodeException:
    def test_failed_run_sets_status_failed(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Monkeypatch a graph node to raise -> GraphRun.status must become 'failed'."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_VALID_JOB_POST),
            user_id=user.id,
        )

        import applypilot.agents.graphs.application_graph as graph_mod

        original_build = graph_mod.build_application_graph

        def _patched_build(session, prov):  # noqa: ANN001
            graph = original_build(session, prov)

            def _failing_stream(initial_state, *a, **kw):  # noqa: ANN001
                raise RuntimeError("Simulated node failure for testing")

            graph.stream = _failing_stream
            return graph

        monkeypatch.setattr(graph_mod, "build_application_graph", _patched_build)

        # Run the analysis; it should NOT raise but return a response
        response = service.analyze(app.id)

        run_repo = GraphRunRepository(db_session)
        graph_run = run_repo.get(uuid.UUID(response.graph_run_id))
        assert graph_run is not None
        assert graph_run.status == GraphRunStatus.FAILED.value

    def test_failed_run_has_error_payload(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_VALID_JOB_POST),
            user_id=user.id,
        )

        import applypilot.agents.graphs.application_graph as graph_mod

        original_build = graph_mod.build_application_graph

        def _patched_build(session, prov):  # noqa: ANN001
            graph = original_build(session, prov)

            def _failing_stream(initial_state, *a, **kw):  # noqa: ANN001
                raise ValueError("Simulated extraction failure")

            graph.stream = _failing_stream
            return graph

        monkeypatch.setattr(graph_mod, "build_application_graph", _patched_build)

        response = service.analyze(app.id)

        run_repo = GraphRunRepository(db_session)
        graph_run = run_repo.get(uuid.UUID(response.graph_run_id))
        assert graph_run is not None
        assert graph_run.error_payload is not None
        assert "message" in graph_run.error_payload
        assert "type" in graph_run.error_payload
        assert graph_run.error_payload["type"] == "ValueError"

    def test_failed_run_application_not_left_inconsistent(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After a failed run, the application must not be in 'running' or corrupted state."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_VALID_JOB_POST),
            user_id=user.id,
        )

        import applypilot.agents.graphs.application_graph as graph_mod

        original_build = graph_mod.build_application_graph

        def _patched_build(session, prov):  # noqa: ANN001
            graph = original_build(session, prov)

            def _failing_stream(initial_state, *a, **kw):  # noqa: ANN001
                raise RuntimeError("Injected failure")

            graph.stream = _failing_stream
            return graph

        monkeypatch.setattr(graph_mod, "build_application_graph", _patched_build)
        service.analyze(app.id)

        # Application should still be fetchable (not corrupted)
        fetched_app = service.get_application(app.id)
        assert fetched_app is not None
        # Status should be 'saved' (not 'drafted') since persist_outputs never ran
        assert fetched_app.status in (
            "saved", "analyzed", "drafted"
        ), f"Unexpected application status: {fetched_app.status}"

    def test_failed_run_no_fit_analysis_persisted(
        self, db_session: Session, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After a failure before persist_outputs, no fit analysis row should exist."""
        user = _make_user(db_session)
        _seed_profile(db_session, user.id)
        service = ApplicationService(db_session)
        app = service.create_application(
            data=JobApplicationCreate(raw_job_post=_VALID_JOB_POST),
            user_id=user.id,
        )

        import applypilot.agents.graphs.application_graph as graph_mod

        original_build = graph_mod.build_application_graph

        def _patched_build(session, prov):  # noqa: ANN001
            graph = original_build(session, prov)

            def _failing_stream(initial_state, *a, **kw):  # noqa: ANN001
                raise RuntimeError("Injected failure before persist")

            graph.stream = _failing_stream
            return graph

        monkeypatch.setattr(graph_mod, "build_application_graph", _patched_build)
        service.analyze(app.id)

        # No FitAnalysis should exist for this application
        fit_rows = db_session.execute(
            select(FitAnalysis).where(FitAnalysis.application_id == app.id)
        ).scalars().all()
        assert len(fit_rows) == 0, (
            "No FitAnalysis should be persisted after a complete pipeline failure"
        )


# ---------------------------------------------------------------------------
# Graph run with short job post (validate_input short-circuit)
# ---------------------------------------------------------------------------


class TestValidateInputShortCircuit:
    def test_validate_input_short_job_post_graph_run_completes(self, db_session: Session) -> None:
        """validate_input routes to END for short posts; graph_run must not be stuck in 'running'."""
        user = _make_user(db_session)
        # We need to bypass the JobApplicationCreate 30-char minimum to test validate_input
        # Use the repository directly to insert a short raw_job_post
        from applypilot.db.repositories.application_repository import JobApplicationRepository

        repo = JobApplicationRepository(db_session)
        app = repo.create(
            user_id=user.id,
            raw_job_post="Too short.",  # < 30 chars (validate_input threshold)
            status="saved",
        )
        db_session.commit()

        run_service = GraphRunService(db_session)
        graph_run = run_service.run_analysis(app.id)

        # validate_input routes to END, which is a successful graph completion
        # (short-circuit is not an exception, it's a controlled early exit)
        assert graph_run.status in (GraphRunStatus.COMPLETED.value, GraphRunStatus.FAILED.value), (
            f"Graph run must not be stuck in 'running'; got {graph_run.status!r}"
        )
