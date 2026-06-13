"""Text chunking utilities for splitting profile-item bodies into evidence chunks.

The main entry point is :func:`chunk_text`, which splits a long document into
overlapping windows sized for embedding (≤ *max_chars* characters each) while
preferring sentence or paragraph boundaries to avoid cutting mid-sentence.
"""

from __future__ import annotations

_DEFAULT_MAX_CHARS: int = 512
_DEFAULT_OVERLAP: int = 50


def chunk_text(
    text: str,
    max_chars: int = _DEFAULT_MAX_CHARS,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[str]:
    """Split *text* into overlapping chunks of at most *max_chars* characters.

    Splitting tries sentence boundaries (``". "``) first, then paragraph
    breaks (``"\\n"``), and finally falls back to a hard character cut.  Each
    consecutive pair of chunks shares up to *overlap* characters from the end
    of the previous chunk to preserve local context.

    Args:
        text:      The raw text to split.
        max_chars: Maximum character length of each chunk (default 512).
        overlap:   Number of trailing characters from the previous chunk
                   to prepend to the next one (default 50).

    Returns:
        A list of non-empty stripped chunk strings.  Returns ``[text]`` when
        ``len(text) <= max_chars``.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start: int = 0

    while start < len(text):
        end = start + max_chars

        if end >= len(text):
            tail = text[start:].strip()
            if tail:
                chunks.append(tail)
            break

        # Prefer sentence boundary: look for ". " within the window.
        split_at = text.rfind(". ", start, end)
        if split_at != -1:
            split_at += 1  # include the period
        else:
            # Fall back to paragraph break.
            split_at = text.rfind("\n", start, end)

        if split_at == -1 or split_at <= start:
            split_at = end

        chunk = text[start:split_at].strip()
        if chunk:
            chunks.append(chunk)

        # Advance with overlap so consecutive chunks share context.
        next_start = split_at - overlap
        start = next_start if next_start > start else split_at

    return chunks


__all__ = ["chunk_text"]
