"""LLM and embedding provider interfaces and implementations for the agent layer.

Exposes the synchronous :class:`LLMProvider` / :class:`EmbeddingProvider`
protocols, the concrete provider classes, and the ``get_*_provider`` factories.
Provider modules import their heavy SDK dependencies lazily, so importing this
package stays cheap regardless of the configured provider.
"""

from __future__ import annotations

from applypilot.agents.llm.anthropic_provider import AnthropicLLMProvider
from applypilot.agents.llm.base import EmbeddingProvider, LLMProvider, T
from applypilot.agents.llm.embeddings import (
    FakeEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from applypilot.agents.llm.factory import get_embedding_provider, get_llm_provider
from applypilot.agents.llm.fake import FakeLLMProvider
from applypilot.agents.llm.ollama_provider import OllamaLLMProvider
from applypilot.agents.llm.openai_provider import OpenAILLMProvider

__all__ = [
    "AnthropicLLMProvider",
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "FakeLLMProvider",
    "LLMProvider",
    "OllamaEmbeddingProvider",
    "OllamaLLMProvider",
    "OpenAIEmbeddingProvider",
    "OpenAILLMProvider",
    "T",
    "get_embedding_provider",
    "get_llm_provider",
]
