"""Synchronous LLM and embedding provider protocols.

These define the *interfaces* the agent layer depends on. Concrete
implementations (fake / openai / anthropic / ollama) are added in a later phase
and MUST satisfy these protocols. Everything here is synchronous per the
ApplyPilot backend convention — no ``async``/``await``.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

# Bound to Pydantic so ``structured`` always returns a validated model instance.
T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """A synchronous large-language-model provider.

    Attributes:
        name: Human-readable provider identifier (e.g. ``"fake"``, ``"openai"``).
        model: The concrete model identifier the provider is configured to use.
    """

    name: str
    model: str

    def structured(self, prompt: str, schema: type[T]) -> T:
        """Return a validated instance of ``schema`` produced from ``prompt``."""
        ...

    def text(self, prompt: str) -> str:
        """Return a free-form text completion for ``prompt``."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """A synchronous text-embedding provider producing 1536-dim vectors."""

    def embed_text(self, text: str) -> list[float]:
        """Return the embedding vector for a single ``text``."""
        ...

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of ``texts``, order-preserving."""
        ...
