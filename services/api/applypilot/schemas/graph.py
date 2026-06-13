"""Schemas for agent graph runs and graph errors."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from applypilot.schemas.common import ORMModel
from applypilot.schemas.enums import GraphRunStatus


class GraphError(BaseModel):
    """A structured error captured during a graph node execution."""

    node: str
    message: str
    type: str


class GraphRunRead(ORMModel):
    """A persisted agent graph run as returned from the API."""

    id: UUID
    application_id: UUID
    graph_name: str
    status: GraphRunStatus
    current_node: str | None = None
    node_timings: dict[str, Any] | None = None
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    model_metadata: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
