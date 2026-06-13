"""Graph-run routes — observe LangGraph agent execution records.

Exposes read-only endpoints for :class:`~applypilot.db.models.GraphRun` records
under the ``/graph-runs`` prefix.  All handlers are **synchronous** (plain ``def``).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from applypilot.api.deps import SessionDep
from applypilot.db.repositories.graph_run_repository import GraphRunRepository
from applypilot.schemas.graph import GraphRunRead
from applypilot.services.application_service import ApplicationService

router = APIRouter(prefix="/graph-runs", tags=["graph-runs"])

OptionalApplicationIdQuery = Annotated[
    uuid.UUID | None,
    Query(alias="application_id", description="Filter graph runs by application ID"),
]


@router.get("", response_model=list[GraphRunRead])
def list_graph_runs(
    session: SessionDep,
    application_id: OptionalApplicationIdQuery = None,
) -> list[GraphRunRead]:
    """List graph runs, optionally filtered by application ID (newest first)."""
    runs = ApplicationService(session).list_graph_runs(application_id=application_id)
    return [GraphRunRead.model_validate(run) for run in runs]


@router.get("/{graph_run_id}", response_model=GraphRunRead)
def get_graph_run(
    graph_run_id: uuid.UUID,
    session: SessionDep,
) -> GraphRunRead:
    """Retrieve a single graph run by ID."""
    run = GraphRunRepository(session).get(graph_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"GraphRun {graph_run_id} not found")
    return GraphRunRead.model_validate(run)
