"""EmbeddingService: thin facade over an EmbeddingProvider with text chunking.

The service is intentionally stateless beyond holding a reference to its
provider — all methods are synchronous, no async/await anywhere.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from applypilot.agents.llm.base import EmbeddingProvider

#: Dimensionality guaranteed by all ApplyPilot embedding providers.
DIM: int = 1536

_DEFAULT_MAX_TOKENS: int = 120
_DEFAULT_OVERLAP: int = 20


class EmbeddingService:
    """Wraps an :class:`~applypilot.agents.llm.base.EmbeddingProvider` with helpers.

    Provides:
    - :meth:`embed_text`  — single-text embedding.
    - :meth:`embed_many`  — batch embedding.
    - :meth:`chunk_text`  — sentence-aware sliding-window chunker.

    Args:
        provider: Any object satisfying the ``EmbeddingProvider`` protocol.
    """

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> list[float]:
        """Return the 1536-dim embedding vector for a single *text*."""
        return self._provider.embed_text(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return 1536-dim embedding vectors for *texts*, preserving order."""
        return self._provider.embed_many(texts)

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        overlap: int = _DEFAULT_OVERLAP,
    ) -> list[str]:
        """Split *text* into overlapping word-based chunks.

        Strategy
        --------
        1. Split the input into sentences on ``[.!?]`` followed by whitespace
           or end-of-string.
        2. Concatenate all sentence words into a flat word list.
        3. Slide a window of *max_tokens* words across the list, stepping
           forward by ``max_tokens - overlap`` words each iteration so
           adjacent chunks share *overlap* words for context continuity.

        Args:
            text:       Raw text to chunk.
            max_tokens: Maximum number of words per chunk (approx. ≈ tokens).
                        Default: 120.
            overlap:    Number of words shared between consecutive chunks.
                        Default: 20.  Must be < *max_tokens*.

        Returns:
            Non-empty list of string chunks.  A text shorter than *max_tokens*
            words is returned as a single-element list.  Empty / whitespace-only
            input returns an empty list.
        """
        if not text or not text.strip():
            return []

        # Clamp overlap so the window always advances
        effective_overlap = max(0, min(overlap, max_tokens - 1))
        step = max_tokens - effective_overlap

        # Sentence-aware split: break on [.!?] followed by whitespace or EOS
        sentences = re.split(r"(?<=[.!?])(?:\s+|$)", text.strip())

        words: list[str] = []
        for sentence in sentences:
            words.extend(sentence.split())

        if not words:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            if end >= len(words):
                break
            start += step

        return chunks
