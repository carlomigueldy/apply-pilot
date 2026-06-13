"""Prompt loader for ApplyPilot agent prompts.

Versioned markdown prompts live as ``{name}.md`` files alongside this package.
Use :func:`load_prompt` to retrieve them; results are cached in-process so
file I/O is paid at most once per unique name per process lifetime.
"""

from __future__ import annotations

import functools
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


@functools.cache
def load_prompt(name: str) -> str:
    """Load and return the content of ``agents/prompts/{name}.md``.

    Results are cached: repeated calls with the same *name* return the same
    string without hitting the filesystem again.

    Args:
        name: Prompt file stem (without the ``.md`` extension), e.g.
            ``"fit_analysis"`` resolves to ``agents/prompts/fit_analysis.md``.

    Returns:
        The full text content of the prompt file.

    Raises:
        FileNotFoundError: When ``agents/prompts/{name}.md`` does not exist.
        ValueError: When *name* contains path separators (security guard).
    """
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"Prompt name must be a simple stem, not a path: {name!r}")

    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt '{name}' not found. Expected file: {path}"
        )
    return path.read_text(encoding="utf-8")
