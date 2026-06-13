"""Provider factories: select embedding (and future LLM) providers from settings.

Usage
-----
    from applypilot.agents.llm.factory import get_embedding_provider

    provider = get_embedding_provider()   # uses process-wide settings
    vector = provider.embed_text("Senior Python engineer")

Phase-3 note: ``get_llm_provider`` raises ``NotImplementedError`` until
concrete LLM provider classes are added in Phase 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from applypilot.agents.llm.base import EmbeddingProvider, LLMProvider
    from applypilot.core.config import Settings


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Return an :class:`~applypilot.agents.llm.base.EmbeddingProvider` instance.

    The concrete provider class is chosen by ``settings.embedding_provider``:

    - ``"fake"``   → :class:`~applypilot.agents.llm.embeddings.FakeEmbeddingProvider`
    - ``"openai"`` → :class:`~applypilot.agents.llm.embeddings.OpenAIEmbeddingProvider`
    - ``"ollama"`` → :class:`~applypilot.agents.llm.embeddings.OllamaEmbeddingProvider`

    Args:
        settings: Optional settings override; defaults to the cached global instance.

    Raises:
        ValueError: If ``settings.embedding_provider`` names an unknown provider.
    """
    from applypilot.core.config import get_settings

    s = settings or get_settings()
    provider_name = s.embedding_provider.strip().lower()

    if provider_name == "fake":
        from applypilot.agents.llm.embeddings import FakeEmbeddingProvider

        return FakeEmbeddingProvider()

    if provider_name == "openai":
        from applypilot.agents.llm.embeddings import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(settings=s)

    if provider_name == "ollama":
        from applypilot.agents.llm.embeddings import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(settings=s)

    raise ValueError(
        f"Unknown embedding provider {provider_name!r}. "
        "Expected one of: 'fake', 'openai', 'ollama'."
    )


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Return an :class:`~applypilot.agents.llm.base.LLMProvider` instance.

    The concrete provider class is chosen by ``settings.llm_provider``:

    - ``"fake"``      → :class:`~applypilot.agents.llm.fake.FakeLLMProvider`
    - ``"openai"``    → :class:`~applypilot.agents.llm.openai_provider.OpenAILLMProvider`
    - ``"anthropic"`` → :class:`~applypilot.agents.llm.anthropic_provider.AnthropicLLMProvider`
    - ``"ollama"``    → :class:`~applypilot.agents.llm.ollama_provider.OllamaLLMProvider`

    Provider modules import their heavy SDK dependencies lazily, so selecting one
    here is cheap and never pulls an SDK that is not in use.

    Args:
        settings: Optional settings override; defaults to the cached global instance.

    Raises:
        ValueError: If ``settings.llm_provider`` names an unknown provider.
    """
    from applypilot.core.config import get_settings

    s = settings or get_settings()
    provider_name = s.llm_provider.strip().lower()

    if provider_name == "fake":
        from applypilot.agents.llm.fake import FakeLLMProvider

        return FakeLLMProvider(settings=s)

    if provider_name == "openai":
        from applypilot.agents.llm.openai_provider import OpenAILLMProvider

        return OpenAILLMProvider(settings=s)

    if provider_name == "anthropic":
        from applypilot.agents.llm.anthropic_provider import AnthropicLLMProvider

        return AnthropicLLMProvider(settings=s)

    if provider_name == "ollama":
        from applypilot.agents.llm.ollama_provider import OllamaLLMProvider

        return OllamaLLMProvider(settings=s)

    raise ValueError(
        f"Unknown LLM provider {provider_name!r}. "
        "Expected one of: 'fake', 'openai', 'anthropic', 'ollama'."
    )
