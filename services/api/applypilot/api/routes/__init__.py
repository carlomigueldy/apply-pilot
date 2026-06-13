"""Central API router aggregator.

``api_router`` is mounted by the application under the ``/api`` prefix. Later
phases register additional sub-routers by appending ``include_router`` calls
below — keep one router per line for clean diffs.
"""

from __future__ import annotations

from fastapi import APIRouter

from applypilot.api.routes import health, profile
from applypilot.api.routes import settings as settings_routes
from applypilot.api.routes.applications import router as applications_router
from applypilot.api.routes.graph_runs import router as graph_runs_router

api_router = APIRouter()

# --- Registered routers (extend in later phases) ---
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(settings_routes.router)
api_router.include_router(applications_router)
api_router.include_router(graph_runs_router)

__all__ = ["api_router"]
