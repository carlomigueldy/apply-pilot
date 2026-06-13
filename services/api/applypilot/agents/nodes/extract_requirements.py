"""``extract_requirements`` node — derive discrete, categorised requirements.

Grounds the ``extract_requirements`` prompt with both the raw post and the
already-extracted job metadata, then asks the provider for a validated
:class:`~applypilot.schemas.jobs.JobRequirementList`.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.base import LLMProvider
from applypilot.agents.nodes._common import append_error, dump
from applypilot.agents.prompts import load_prompt
from applypilot.agents.state import ApplicationGraphState
from applypilot.schemas.jobs import JobRequirementList


def extract_requirements(
    provider: LLMProvider, state: ApplicationGraphState
) -> dict[str, Any]:
    """Produce ``{'requirements': [JobRequirement, ...]}``.

    Args:
        provider: Injected LLM provider (bound by the graph factory).
        state: Current graph state; ``raw_job_post`` and ``extracted_job`` read.

    Returns:
        Partial state with the parsed ``requirements`` list, or an ``errors``
        update if the provider call fails.
    """
    try:
        context = {
            "raw_job_post": state["raw_job_post"],
            "extracted_job": dump(state.get("extracted_job")),
        }
        prompt = load_prompt("extract_requirements") + build_context_block(context)
        result = provider.structured(prompt, JobRequirementList)
        return {"requirements": list(result.requirements)}
    except Exception as exc:
        return {
            "errors": append_error(
                state, "extract_requirements", str(exc), type(exc).__name__
            )
        }
