"""Concrete EmbeddingProvider implementations.

All providers are synchronous — no async/await anywhere.

Providers
---------
FakeEmbeddingProvider   — deterministic token-hash BoW, no network, no API key.
OpenAIEmbeddingProvider — openai sync client (lazy import).
OllamaEmbeddingProvider — httpx sync POST to a local Ollama server.
"""

from __future__ import annotations

import hashlib
import math
import re
from functools import cached_property
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from applypilot.core.config import Settings

DIM: int = 1536
_TOKEN_DIMS: int = 4  # distinct dimensions each token activates (reduces collisions)
_TOKEN_RE = re.compile(r"[a-z0-9]+")

# English function words only — deliberately excludes domain/signal vocabulary
# (e.g. "production", "engineering", "experience") so they still contribute.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "of", "for", "to", "in", "on", "at",
        "by", "with", "from", "as", "is", "are", "was", "were", "be", "been",
        "being", "am", "this", "that", "these", "those", "it", "its", "you",
        "he", "she", "we", "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "our", "their", "mine", "yours", "ours", "theirs", "has", "have",
        "had", "having", "do", "does", "did", "doing", "will", "would", "shall",
        "should", "can", "could", "may", "might", "must", "not", "no", "nor",
        "so", "than", "then", "too", "very", "just", "also", "if", "else", "when",
        "while", "where", "which", "who", "whom", "whose", "what", "how", "why",
        "into", "over", "under", "out", "up", "down", "off", "about", "across",
        "after", "before", "between", "through", "during", "per", "via", "within",
    }
)


class FakeEmbeddingProvider:
    """Deterministic 1536-dim embeddings for tests and local development.

    Algorithm (sparse positive bag-of-words)
    -----------------------------------------
    1. Tokenise *text* on ``[a-z0-9]+`` after lower-casing (so "Next.js" →
       ``next``, ``js`` and "React," → ``react``), drop single-char tokens and
       English function words.
    2. Each surviving token activates ``_TOKEN_DIMS`` dimensions (derived from
       non-overlapping 4-byte windows of its SHA-256 digest) by ``+1.0``.
    3. L2-normalise to unit length.

    The vector is *sparse and positive*: two texts that share distinctive tokens
    land on the same dimensions and gain positive cosine similarity, while texts
    with disjoint vocabulary are near-orthogonal (cosine ≈ 0). This makes shared
    keywords — not a dense baseline — drive ranking, the property evidence search
    relies on. SHA-256 is deterministic, so the same text always yields the same
    vector and no network call is made.
    """

    def embed_text(self, text: str) -> list[float]:
        """Return the deterministic 1536-dim embedding vector for *text*."""
        vec = [0.0] * DIM
        tokens = [
            t for t in _TOKEN_RE.findall(text.lower())
            if len(t) > 1 and t not in _STOPWORDS
        ]

        for token in tokens:
            digest: bytes = hashlib.sha256(token.encode()).digest()  # 32 bytes
            for k in range(_TOKEN_DIMS):
                idx = int.from_bytes(digest[k * 4 : k * 4 + 4], "big") % DIM
                vec[idx] += 1.0

        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-12:
            # Degenerate: empty / stopword-only text → deterministic unit vector
            fallback = int.from_bytes(hashlib.sha256(text.lower().encode()).digest()[:4], "big")
            vec[fallback % DIM] = 1.0
            return vec

        return [x / norm for x in vec]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for each text in *texts*, preserving order."""
        return [self.embed_text(t) for t in texts]


class OpenAIEmbeddingProvider:
    """Sync OpenAI embedding provider (text-embedding-3-small / large / ada-002).

    The ``openai`` package is imported lazily on first use so that the rest of
    the application does not require it when a different provider is active.

    Args:
        settings: Optional :class:`~applypilot.core.config.Settings` override.
                  Defaults to the process-wide cached settings instance.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        if not s.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured in settings")
        self._api_key: str = s.openai_api_key
        self._model: str = s.embedding_model

    @cached_property
    def _client(self):  # type: ignore[return]
        """Lazy singleton openai.OpenAI sync client."""
        import openai  # lazy import — only pulled when first needed

        return openai.OpenAI(api_key=self._api_key)

    def embed_text(self, text: str) -> list[float]:
        """Embed a single *text* via the OpenAI Embeddings API."""
        response = self._client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of *texts* in a single OpenAI API call."""
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        # API guarantees results are returned in input order; sort by index for safety.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]


class OllamaEmbeddingProvider:
    """Sync embedding provider backed by a local Ollama server.

    Uses ``httpx`` (synchronous) to POST to ``<ollama_base_url>/api/embeddings``.

    Args:
        settings: Optional :class:`~applypilot.core.config.Settings` override.
                  Defaults to the process-wide cached settings instance.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        from applypilot.core.config import get_settings

        s = settings or get_settings()
        self._base_url: str = s.ollama_base_url.rstrip("/")
        self._model: str = s.embedding_model

    def _post_embedding(self, text: str) -> list[float]:
        """POST a single embedding request to the Ollama server."""
        url = f"{self._base_url}/api/embeddings"
        resp = httpx.post(
            url,
            json={"model": self._model, "prompt": text},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    def embed_text(self, text: str) -> list[float]:
        """Embed a single *text* via the local Ollama server."""
        return self._post_embedding(text)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed each text in *texts* sequentially via the Ollama server."""
        return [self._post_embedding(t) for t in texts]
