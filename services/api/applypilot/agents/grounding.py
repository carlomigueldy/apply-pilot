"""Grounding convention helpers for passing structured context to LLM prompts.

Nodes ground an LLM call by appending a marked JSON block to the prompt::

    <<CONTEXT_JSON>>{ ...json... }<</CONTEXT_JSON>>

:class:`~applypilot.agents.llm.fake.FakeLLMProvider` parses this block to produce
deterministic, schema-valid, grounded outputs (the linchpin of deterministic
testing). Real providers ignore the markers entirely — to them the block is just
additional context text.

Everything here is synchronous and dependency-free (stdlib ``json`` only).
"""

from __future__ import annotations

import json
from typing import Any

# Public markers so providers (and tests) can locate / strip the block without
# re-deriving the literals.
CONTEXT_OPEN = "<<CONTEXT_JSON>>"
CONTEXT_CLOSE = "<</CONTEXT_JSON>>"


def build_context_block(data: dict[str, Any]) -> str:
    """Serialise *data* into the marked ``CONTEXT_JSON`` block.

    The payload is encoded with ``json.dumps(..., default=str)`` so non-JSON
    primitives (``UUID``, ``datetime``, ``Enum`` values, etc.) serialise to their
    string form rather than raising.

    Args:
        data: Arbitrary JSON-serialisable mapping of grounding context.

    Returns:
        The context text to append to a prompt, e.g.
        ``"<<CONTEXT_JSON>>{\"k\": \"v\"}<</CONTEXT_JSON>>"``.
    """
    payload = json.dumps(data, default=str)
    return f"{CONTEXT_OPEN}{payload}{CONTEXT_CLOSE}"


def parse_context_block(prompt: str) -> dict[str, Any]:
    """Extract and parse the ``CONTEXT_JSON`` block from *prompt*.

    Robust by design: returns an empty ``dict`` when the markers are absent, the
    block is malformed/incomplete, the JSON is invalid, or the decoded value is
    not a JSON object. Never raises.

    The *last* opening marker is used so a block appended at the end of a prompt
    wins over any marker-like text that may appear earlier in instructions.

    Args:
        prompt: The full prompt string, possibly containing a context block.

    Returns:
        The parsed context mapping, or ``{}`` when none is recoverable.
    """
    start = prompt.rfind(CONTEXT_OPEN)
    if start == -1:
        return {}
    start += len(CONTEXT_OPEN)
    end = prompt.find(CONTEXT_CLOSE, start)
    if end == -1:
        return {}

    raw = prompt[start:end]
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def strip_context_block(prompt: str) -> str:
    """Return *prompt* with a trailing ``CONTEXT_JSON`` block removed, if present.

    Used to recover the human-readable instruction portion of a prompt (e.g. for
    deterministic ``text`` completions). Returns the original prompt unchanged
    when no complete block is found.
    """
    start = prompt.rfind(CONTEXT_OPEN)
    if start == -1:
        return prompt
    end = prompt.find(CONTEXT_CLOSE, start + len(CONTEXT_OPEN))
    if end == -1:
        return prompt
    return prompt[:start] + prompt[end + len(CONTEXT_CLOSE) :]
