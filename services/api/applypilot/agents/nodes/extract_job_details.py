"""``extract_job_details`` node — parse the raw post into a structured job.

Grounds the ``extract_job_details`` prompt with the raw job post via the
``CONTEXT_JSON`` convention and asks the injected provider for a validated
:class:`~applypilot.schemas.jobs.ExtractedJob`.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.base import LLMProvider
from applypilot.agents.nodes._common import append_error
from applypilot.agents.prompts import load_prompt
from applypilot.agents.state import ApplicationGraphState
from applypilot.schemas.jobs import ExtractedJob


def extract_job_details(
    provider: LLMProvider, state: ApplicationGraphState
) -> dict[str, Any]:
    """Produce ``{'extracted_job': ExtractedJob}`` from ``state['raw_job_post']``.

    Args:
        provider: Injected LLM provider (bound by the graph factory).
        state: Current graph state; ``raw_job_post`` is read.

    Returns:
        Partial state with the parsed ``extracted_job``, or an ``errors`` update
        if the provider call fails.
    """
    try:
        prompt = load_prompt("extract_job_details") + build_context_block(
            {"raw_job_post": state["raw_job_post"]}
        )
        extracted = provider.structured(prompt, ExtractedJob)
        return {"extracted_job": extracted}
    except Exception as exc:
        return {
            "errors": append_error(
                state, "extract_job_details", str(exc), type(exc).__name__
            )
        }
