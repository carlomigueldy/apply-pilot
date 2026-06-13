"""Unit tests for the embedding (and LLM) provider factory functions.

Verifies:
- get_embedding_provider returns FakeEmbeddingProvider when embedding_provider="fake".
- The returned provider satisfies the EmbeddingProvider protocol.
- Unknown provider names raise ValueError.
- get_llm_provider raises NotImplementedError for non-fake providers (Phase-2 stub).
"""

from __future__ import annotations

import pytest

from applypilot.agents.llm.base import EmbeddingProvider
from applypilot.agents.llm.embeddings import FakeEmbeddingProvider
from applypilot.agents.llm.factory import get_embedding_provider
from applypilot.core.config import Settings


def _settings(**overrides) -> Settings:
    """Create a Settings instance with sensible test defaults."""
    base = {
        "database_url": "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot_test",
        "llm_provider": "fake",
        "embedding_provider": "fake",
        "test_mode": True,
    }
    return Settings(**{**base, **overrides})


class TestGetEmbeddingProvider:
    def test_fake_provider_returns_fake_embedding_provider(self) -> None:
        """get_embedding_provider('fake') must return a FakeEmbeddingProvider."""
        settings = _settings(embedding_provider="fake")
        provider = get_embedding_provider(settings)
        assert isinstance(provider, FakeEmbeddingProvider)

    def test_fake_provider_satisfies_protocol(self) -> None:
        """Returned provider must satisfy the EmbeddingProvider protocol."""
        settings = _settings(embedding_provider="fake")
        provider = get_embedding_provider(settings)
        # runtime_checkable Protocol check
        assert isinstance(provider, EmbeddingProvider)

    def test_fake_provider_can_embed(self) -> None:
        """Provider returned by factory must be callable for embedding."""
        settings = _settings(embedding_provider="fake")
        provider = get_embedding_provider(settings)
        vec = provider.embed_text("test sentence")
        assert len(vec) == 1536
        assert all(isinstance(x, float) for x in vec)

    def test_unknown_provider_raises_value_error(self) -> None:
        """Unrecognised embedding_provider names must raise ValueError."""
        settings = _settings(embedding_provider="unknown_provider_xyz")
        with pytest.raises(ValueError, match="unknown_provider_xyz"):
            get_embedding_provider(settings)

    def test_provider_name_case_insensitive(self) -> None:
        """Provider name lookup is case-insensitive."""
        settings = _settings(embedding_provider="FAKE")
        provider = get_embedding_provider(settings)
        assert isinstance(provider, FakeEmbeddingProvider)

    def test_provider_name_strips_whitespace(self) -> None:
        """Leading/trailing whitespace in provider name is tolerated."""
        settings = _settings(embedding_provider="  fake  ")
        provider = get_embedding_provider(settings)
        assert isinstance(provider, FakeEmbeddingProvider)

    def test_multiple_calls_return_independent_instances(self) -> None:
        """Each call returns a fresh provider instance (no shared state)."""
        settings = _settings(embedding_provider="fake")
        p1 = get_embedding_provider(settings)
        p2 = get_embedding_provider(settings)
        # Should be independent objects (though same type)
        assert type(p1) is type(p2)
        # Embeddings should still be equal (deterministic)
        assert p1.embed_text("hello") == p2.embed_text("hello")


class TestGetLLMProvider:
    def test_get_llm_provider_fake_not_implemented(self) -> None:
        """get_llm_provider is a Phase-3 stub; non-implemented providers raise."""
        from applypilot.agents.llm.factory import get_llm_provider

        settings = _settings(llm_provider="openai")
        with pytest.raises((NotImplementedError, ValueError)):
            get_llm_provider(settings)
