"""Integration tests for the /api/health endpoint.

Tests the liveness/readiness probe without hitting a live database by mocking
check_db.  The DB-connectivity path is covered when the full test suite runs
against the test database.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client: TestClient) -> None:
        """GET /api/health must always return HTTP 200."""
        with patch("applypilot.api.routes.health.check_db", return_value=True):
            response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_status_ok_when_db_up(self, client: TestClient) -> None:
        """When check_db returns True, status must be 'ok'."""
        with patch("applypilot.api.routes.health.check_db", return_value=True):
            response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "ok"

    def test_health_status_degraded_when_db_down(self, client: TestClient) -> None:
        """When check_db returns False, status must be 'degraded'."""
        with patch("applypilot.api.routes.health.check_db", return_value=False):
            response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["db"] == "down"

    def test_health_response_schema(self, client: TestClient) -> None:
        """Response must include all expected fields."""
        with patch("applypilot.api.routes.health.check_db", return_value=True):
            response = client.get("/api/health")
        data = response.json()
        required_keys = {"status", "app", "env", "llm_provider", "provider_is_local", "db"}
        assert required_keys.issubset(data.keys()), (
            f"Missing keys: {required_keys - data.keys()}"
        )

    def test_health_app_name(self, client: TestClient) -> None:
        """Response must report the application name."""
        with patch("applypilot.api.routes.health.check_db", return_value=True):
            response = client.get("/api/health")
        data = response.json()
        assert data["app"] == "ApplyPilot"

    def test_health_llm_provider_is_fake(self, client: TestClient) -> None:
        """In test mode the LLM provider should be 'fake'."""
        with patch("applypilot.api.routes.health.check_db", return_value=True):
            response = client.get("/api/health")
        data = response.json()
        assert data["llm_provider"] == "fake"
        assert data["provider_is_local"] is True


@pytest.mark.parametrize("path", ["/api/health"])
def test_health_endpoint_is_reachable(client: TestClient, path: str) -> None:
    """Smoke-test: the health endpoint must be registered."""
    with patch("applypilot.api.routes.health.check_db", return_value=True):
        response = client.get(path)
    assert response.status_code == 200
