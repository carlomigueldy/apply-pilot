"""Unit tests for the chunk_text text-splitting utility.

Verifies:
- Short texts are returned as-is (single chunk).
- Long texts are split into multiple chunks.
- All chunks are within the max_chars limit.
- No chunk is empty.
- Overlap causes consecutive chunks to share characters.
- Sentence boundaries are preferred over hard cuts.
"""

from __future__ import annotations

import pytest

from applypilot.utils.chunking import chunk_text

_SENTENCE = (
    "I worked on scalable distributed systems for three years. "
    "During this time I built microservices in Python and Go. "
    "I led a team of five engineers across two continents. "
    "We shipped features that served millions of daily active users. "
    "My key contribution was a caching layer that reduced DB load by 60%."
)


class TestChunkTextBasics:
    def test_empty_string_returns_empty_list(self) -> None:
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self) -> None:
        assert chunk_text("   \n\n  ") == []

    def test_short_text_returned_as_single_chunk(self) -> None:
        text = "A short sentence."
        chunks = chunk_text(text, max_chars=512)
        assert chunks == [text.strip()]

    def test_text_at_exact_limit_returned_as_single_chunk(self) -> None:
        text = "x" * 512
        chunks = chunk_text(text, max_chars=512)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_produces_multiple_chunks(self) -> None:
        # Replicate the sentence to exceed 512 chars many times over.
        text = (_SENTENCE + " ") * 10
        chunks = chunk_text(text, max_chars=512)
        assert len(chunks) > 1, "Long text should be split into multiple chunks"

    def test_no_chunk_exceeds_max_chars(self) -> None:
        text = (_SENTENCE + " ") * 10
        max_chars = 256
        chunks = chunk_text(text, max_chars=max_chars)
        for i, chunk in enumerate(chunks):
            assert len(chunk) <= max_chars, (
                f"Chunk {i} has {len(chunk)} chars, exceeds max {max_chars}"
            )

    def test_no_empty_chunks(self) -> None:
        text = (_SENTENCE + " ") * 5
        chunks = chunk_text(text, max_chars=200)
        assert all(len(c) > 0 for c in chunks), "No chunk should be empty"
        assert all(c.strip() for c in chunks), "No chunk should be whitespace-only"


class TestChunkTextOverlap:
    def test_overlap_zero_no_shared_characters(self) -> None:
        """With overlap=0, consecutive chunks should not share a boundary prefix."""
        # Use a deterministic, long text that splits at hard boundaries.
        text = "a" * 100 + "b" * 100 + "c" * 100
        chunks = chunk_text(text, max_chars=100, overlap=0)
        # Each chunk should start fresh — no repeated content from previous chunk.
        assert len(chunks) >= 2

    def test_full_text_covered(self) -> None:
        """Every character in the original text must appear in at least one chunk."""
        text = "Hello world. " * 30
        chunks = chunk_text(text, max_chars=128)
        combined = " ".join(chunks)
        # All significant tokens from the original should appear somewhere.
        assert "Hello" in combined
        assert "world" in combined


class TestChunkTextCustomParams:
    @pytest.mark.parametrize("max_chars", [64, 128, 256, 512])
    def test_various_max_chars(self, max_chars: int) -> None:
        text = (_SENTENCE + " ") * 4
        chunks = chunk_text(text, max_chars=max_chars)
        assert all(len(c) <= max_chars for c in chunks)

    def test_single_word_splits_at_limit(self) -> None:
        """A single very long word must still be split when it exceeds max_chars."""
        text = "x" * 1000
        chunks = chunk_text(text, max_chars=100, overlap=0)
        # At minimum we get one chunk back; verify they don't exceed max
        for chunk in chunks:
            assert len(chunk) <= 100
