"""GraphRun repository: create, status updates, and listing for LangGraph runs."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import GraphRun


class GraphRunRepository:
    """Create and manage :class:`~applypilot.db.models.GraphRun` records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        application_id: uuid.UUID,
        graph_name: str,
        status: str = "running",
        input_payload: dict[str, Any] | None = None,
        model_metadata: dict[str, Any] | None = None,
    ) -> GraphRun:
        """Persist a new graph run record and flush to assign a DB-generated id."""
        run = GraphRun(
            application_id=application_id,
            graph_name=graph_name,
            status=status,
            input_payload=input_payload or {},
            model_metadata=model_metadata or {},
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, graph_run_id: uuid.UUID) -> GraphRun | None:
        """Return the graph run with *graph_run_id*, or ``None``."""
        stmt = select(GraphRun).where(GraphRun.id == graph_run_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_application(self, application_id: uuid.UUID) -> Sequence[GraphRun]:
        """Return all graph runs for an application, most-recent first."""
        stmt = (
            select(GraphRun)
            .where(GraphRun.application_id == application_id)
            .order_by(GraphRun.started_at.desc())
        )
        return self.session.execute(stmt).scalars().all()

    def update_status(
        self,
        graph_run_id: uuid.UUID,
        status: str,
        current_node: str | None = None,
        node_timings: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        error_payload: dict[str, Any] | None = None,
        completed_at: datetime | None = None,
    ) -> GraphRun | None:
        """Update the execution state of a graph run.

        Only non-``None`` keyword arguments overwrite the stored value, so
        callers can update ``status`` alone without clobbering existing timing
        or payload data.

        Returns the updated :class:`~applypilot.db.models.GraphRun` or
        ``None`` when *graph_run_id* does not exist.
        """
        run = self.get(graph_run_id)
        if run is None:
            return None
        run.status = status
        if current_node is not None:
            run.current_node = current_node
        if node_timings is not None:
            run.node_timings = node_timings
        if output_payload is not None:
            run.output_payload = output_payload
        if error_payload is not None:
            run.error_payload = error_payload
        if completed_at is not None:
            run.completed_at = completed_at
        self.session.flush()
        return run
