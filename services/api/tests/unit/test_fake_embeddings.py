"""Unit tests for FakeEmbeddingProvider.

Verifies:
- Determinism: identical text always yields the same vector.
- Dimensionality: vectors are exactly 1536-dim.
- Normalization: L2 norm is 1.0 (within float tolerance).
- Semantic ordering: texts that share keywords have higher cosine similarity
  to the query than unrelated texts.
- embed_many: delegates to embed_text and preserves order.
"""

from __future__ import annotations

import math

import pytest

from applypilot.agents.llm.embeddings import FakeEmbeddingProvider

_DIM = 1536


@pytest.fixture(scope="module")
def provider() -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cosine(a: list[float], b: list[float]) -> float:
    """Return cosine similarity between two unit vectors (dot product)."""
    return sum(x * y for x, y in zip(a, b, strict=True))


def _l2_norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_text_returns_same_vector(self, provider: FakeEmbeddingProvider) -> None:
        text = "Senior Python engineer with FastAPI experience"
        v1 = provider.embed_text(text)
        v2 = provider.embed_text(text)
        assert v1 == v2, "embed_text must be deterministic for identical input"

    def test_different_texts_differ(self, provider: FakeEmbeddingProvider) -> None:
        v1 = provider.embed_text("Python backend engineer")
        v2 = provider.embed_text("Solidity smart contract developer")
        assert v1 != v2, "Different texts must produce different vectors"


# ---------------------------------------------------------------------------
# Dimensionality
# ---------------------------------------------------------------------------


class TestDimensionality:
    def test_dim_1536(self, provider: FakeEmbeddingProvider) -> None:
        v = provider.embed_text("test text")
        assert len(v) == _DIM, f"Expected {_DIM}-dim vector, got {len(v)}"

    def test_all_floats(self, provider: FakeEmbeddingProvider) -> None:
        v = provider.embed_text("All floats check")
        assert all(isinstance(x, float) for x in v)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


class TestNormalization:
    @pytest.mark.parametrize(
        "text",
        [
            "React TypeScript frontend engineer",
            "Solidity Web3 Ethereum smart contracts",
            "LangGraph RAG LLM AI agents pipeline",
            "a",  # minimal input
        ],
    )
    def test_unit_norm(self, provider: FakeEmbeddingProvider, text: str) -> None:
        v = provider.embed_text(text)
        norm = _l2_norm(v)
        assert abs(norm - 1.0) < 1e-6, f"L2 norm for {text!r} is {norm}, expected 1.0"


# ---------------------------------------------------------------------------
# Shared-keyword similarity
# ---------------------------------------------------------------------------


class TestKeywordSimilarity:
    def test_shared_keyword_ranks_higher_than_unrelated(
        self, provider: FakeEmbeddingProvider
    ) -> None:
        """A text sharing keywords with the query must score higher than an unrelated one."""
        query = "Next.js React production frontend"
        related = "Senior Next.js engineer production deployment React TypeScript"
        unrelated = "PostgreSQL database replication latency tuning"

        q_vec = provider.embed_text(query)
        rel_vec = provider.embed_text(related)
        unrel_vec = provider.embed_text(unrelated)

        sim_related = _cosine(q_vec, rel_vec)
        sim_unrelated = _cosine(q_vec, unrel_vec)

        assert sim_related > sim_unrelated, (
            f"Related text similarity ({sim_related:.4f}) must exceed "
            f"unrelated ({sim_unrelated:.4f}) for query {query!r}"
        )

    def test_web3_query_similarity(self, provider: FakeEmbeddingProvider) -> None:
        query = "Web3 Ethereum blockchain engineering"
        related = "Web3 Solidity smart contracts Ethereum blockchain DeFi"
        unrelated = "React UI components TypeScript frontend design system"

        q_vec = provider.embed_text(query)
        rel_sim = _cosine(q_vec, provider.embed_text(related))
        unrel_sim = _cosine(q_vec, provider.embed_text(unrelated))

        assert rel_sim > unrel_sim

    def test_ai_query_similarity(self, provider: FakeEmbeddingProvider) -> None:
        query = "AI agents LLM RAG pipeline"
        related = "LangGraph LLM agents RAG retrieval pipeline embeddings"
        unrelated = "SQL database indexing B-tree performance"

        q_vec = provider.embed_text(query)
        rel_sim = _cosine(q_vec, provider.embed_text(related))
        unrel_sim = _cosine(q_vec, provider.embed_text(unrelated))

        assert rel_sim > unrel_sim


# ---------------------------------------------------------------------------
# embed_many
# ---------------------------------------------------------------------------


class TestEmbedMany:
    def test_embed_many_matches_embed_text(self, provider: FakeEmbeddingProvider) -> None:
        texts = [
            "Python backend engineer",
            "Next.js React frontend developer",
            "Kubernetes DevOps infrastructure",
        ]
        batch = provider.embed_many(texts)
        singles = [provider.embed_text(t) for t in texts]

        assert len(batch) == len(texts)
        for i, (b, s) in enumerate(zip(batch, singles, strict=True)):
            assert b == s, f"embed_many[{i}] differs from embed_text"

    def test_embed_many_preserves_order(self, provider: FakeEmbeddingProvider) -> None:
        texts = ["alpha text", "beta text", "gamma text"]
        batch = provider.embed_many(texts)
        # Verify each matches its single embed, confirming order
        for text, vec in zip(texts, batch, strict=True):
            assert vec == provider.embed_text(text)

    def test_embed_many_empty(self, provider: FakeEmbeddingProvider) -> None:
        result = provider.embed_many([])
        assert result == []
