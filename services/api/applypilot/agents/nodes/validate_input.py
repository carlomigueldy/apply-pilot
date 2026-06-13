"""``validate_input`` node — guard the raw job post before any LLM work.

This is the graph's entry node. It performs the single cheap pre-condition
check that protects every downstream LLM/DB call: the raw job post must contain
enough real content to be worth analysing. On failure it records a
:class:`~applypilot.schemas.graph.GraphError` so the conditional edge can route
straight to ``END`` without spending tokens.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.nodes._common import append_error
from applypilot.agents.state import ApplicationGraphState

#: Minimum number of non-whitespace characters a job post must contain.
MIN_JOB_POST_LENGTH: int = 30


def validate_input(state: ApplicationGraphState) -> dict[str, Any]:
    """Validate ``state['raw_job_post']``.

    Returns an empty partial state when the post is acceptable. When the post is
    missing or shorter than :data:`MIN_JOB_POST_LENGTH` characters (after
    trimming), an error is appended to the ``errors`` channel and the graph's
    conditional edge short-circuits to ``END``.
    """
    raw = (state.get("raw_job_post") or "").strip()
    if len(raw) < MIN_JOB_POST_LENGTH:
        return {
            "errors": append_error(
                state,
                "validate_input",
                (
                    f"raw_job_post is too short ({len(raw)} chars); "
                    f"at least {MIN_JOB_POST_LENGTH} characters of content are required."
                ),
                "InvalidInputError",
            )
        }
    return {}
