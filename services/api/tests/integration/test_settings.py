"""Integration tests for the /api/settings endpoint.

Verifies the public settings schema is returned correctly and exposes provider
fields that clients need to adapt their behaviour (e.g. show offline badge).
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestSettingsEndpoint:
    def test_settings_returns_200(self, client: TestClient) -> None:
        """GET /api/settings must return HTTP 200."""
        response = client.get("/api/settings")
        assert response.status_code == 200

    def test_settings_response_has_provider_fields(self, client: TestClient) -> None:
        """Response must include all provider-related fields."""
        response = client.get("/api/settings")
        data = response.json()
        required = {
            "app_env",
            "app_name",
            "llm_provider",
            "llm_model",
            "embedding_provider",
            "embedding_model",
            "test_mode",
            "provider_is_local",
        }
        missing = required - data.keys()
        assert not missing, f"Missing fields in /api/settings response: {missing}"

    def test_settings_llm_provider_is_string(self, client: TestClient) -> None:
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["llm_provider"], str)
        assert len(data["llm_provider"]) > 0

    def test_settings_embedding_provider_is_string(self, client: TestClient) -> None:
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["embedding_provider"], str)
        assert len(data["embedding_provider"]) > 0

    def test_settings_provider_is_local_is_bool(self, client: TestClient) -> None:
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["provider_is_local"], bool)

    def test_settings_test_mode_is_bool(self, client: TestClient) -> None:
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["test_mode"], bool)

    def test_settings_fake_provider_is_local(self, client: TestClient) -> None:
        """'fake' provider must be reported as local (no external API)."""
        response = client.get("/api/settings")
        data = response.json()
        if data["llm_provider"] == "fake":
            assert data["provider_is_local"] is True

    def test_settings_app_name_present(self, client: TestClient) -> None:
        response = client.get("/api/settings")
        data = response.json()
        assert data["app_name"] == "ApplyPilot"
