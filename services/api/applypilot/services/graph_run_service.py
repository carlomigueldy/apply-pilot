"""Graph run orchestration service for the application-analysis pipeline.

:class:`GraphRunService` drives a single full run of :func:`build_application_graph`
against a :class:`~applypilot.db.models.JobApplication`, persisting the
:class:`~applypilot.db.models.GraphRun` lifecycle record and committing (or rolling
back) all database writes produced by the graph nodes.

All operations are **synchronous** — no async/await.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

import applypilot.agents.graphs.application_graph as _app_graph
from applypilot.agents.llm.factory import get_llm_provider
from applypilot.agents.state import ApplicationGraphState
from applypilot.core.config import get_settings
from applypilot.db.models import GraphRun
from applypilot.db.repositories.application_repository import JobApplicationRepository
from applypilot.db.repositories.evidence_repository import FitAnalysisRepository
from applypilot.db.repositories.graph_run_repository import GraphRunRepository


class GraphRunService:
    """Drive the application-analysis graph and manage its :class:`GraphRun` record.

    Args:
        session: A bound, synchronous SQLAlchemy session.  The service owns
            all commit/rollback decisions; callers must not commit externally.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def run_analysis(self, application_id: uuid.UUID) -> GraphRun:
        """Execute the full application-analysis graph and persist the result.

        Lifecycle:
        1. Load the application; raise :exc:`ValueError` if not found.
        2. Instantiate the LLM provider and compiled graph.
        3. Persist a ``running`` :class:`~applypilot.db.models.GraphRun` and commit.
        4. Stream the graph, capturing per-node wall-clock timings.
        5. On success: commit the ``persist_outputs`` writes, update the run to
           ``completed`` with output payload and model metadata, commit again.
        6. On exception: rollback the graph writes, update the run to ``failed``
           with an error payload, commit the failed record.
        7. Return the final :class:`~applypilot.db.models.GraphRun` (never ``running``).

        Args:
            application_id: UUID of the job application to analyse.

        Returns:
            The updated :class:`~applypilot.db.models.GraphRun` record.

        Raises:
            ValueError: When *application_id* does not exist in the database.
        """
        app_repo = JobApplicationRepository(self._session)
        run_repo = GraphRunRepository(self._session)

        application = app_repo.get(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")

        settings = get_settings()
        provider = get_llm_provider(settings)
        graph = _app_graph.build_application_graph(self._session, provider)

        graph_run = run_repo.create(
            application_id=application_id,
            graph_name=_app_graph.GRAPH_NAME,
            status="running",
            input_payload={
                "application_id": str(application_id),
                "raw_job_post_preview": application.raw_job_post[:200],
            },
            model_metadata={"provider": provider.name, "model": provider.model},
        )
        self._session.commit()

        graph_run_id: uuid.UUID = graph_run.id

        initial_state: ApplicationGraphState = {
            "application_id": str(application_id),
            "raw_job_post": application.raw_job_post,
            "user_id": str(application.user_id),
        }

        node_timings: dict[str, float] = {}
        current_node: str | None = None
        wall_start = time.monotonic()

        try:
            for chunk in graph.stream(initial_state):
                for node_name in chunk:
                    elapsed = time.monotonic() - wall_start
                    node_timings[node_name] = round(elapsed, 3)
                    current_node = node_name

            self._session.commit()

            latest_fit = FitAnalysisRepository(self._session).get_latest_by_application(
                application_id
            )
            output_payload: dict[str, Any] = {
                "fit_score": latest_fit.fit_score if latest_fit else None,
                "summary": latest_fit.summary if latest_fit else None,
            }

            updated = run_repo.update_status(
                graph_run_id,
                status="completed",
                current_node=current_node,
                node_timings=node_timings,
                output_payload=output_payload,
                completed_at=datetime.now(UTC),
            )
            if updated is not None:
                updated.model_metadata = {"provider": provider.name, "model": provider.model}
                self._session.flush()
            self._session.commit()

        except Exception as exc:
            try:
                self._session.rollback()
            except Exception:  # noqa: BLE001
                pass

            failed_node = current_node or "unknown"
            try:
                run_repo.update_status(
                    graph_run_id,
                    status="failed",
                    current_node=failed_node,
                    node_timings=node_timings or None,
                    error_payload={
                        "node": failed_node,
                        "message": str(exc),
                        "type": type(exc).__name__,
                    },
                    completed_at=datetime.now(UTC),
                )
                self._session.commit()
            except Exception:  # noqa: BLE001
                pass

        result = run_repo.get(graph_run_id)
        return result if result is not None else graph_run
