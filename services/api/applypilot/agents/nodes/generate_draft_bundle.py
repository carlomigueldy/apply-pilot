"""``generate_draft_bundle`` node — write the application materials.

Grounds the ``draft_bundle`` prompt with the extracted job, the fit summary and
positioning strategy, the top retrieved evidence, and the requested tone/length/
draft types, then asks the provider for a validated
:class:`~applypilot.schemas.drafts.DraftBundle`.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.grounding import build_context_block
from applypilot.agents.llm.base import LLMProvider
from applypilot.agents.nodes._common import append_error, attr, dump
from applypilot.agents.prompts import load_prompt
from applypilot.agents.state import ApplicationGraphState
from applypilot.schemas.drafts import DraftBundle
from applypilot.schemas.enums import DraftLength, DraftType, Tone

#: Maximum evidence snippets fed to the draft prompt for grounding.
TOP_EVIDENCE_LIMIT: int = 8

#: Draft types generated when the caller does not request a specific subset.
DEFAULT_DRAFT_TYPES: tuple[str, ...] = tuple(member.value for member in DraftType)


def generate_draft_bundle(
    provider: LLMProvider, state: ApplicationGraphState
) -> dict[str, Any]:
    """Produce ``{'draft_bundle': DraftBundle}`` grounded in the job and evidence.

    Args:
        provider: Injected LLM provider.
        state: Current graph state; ``extracted_job``, ``fit_analysis``,
            ``retrieved_evidence`` and the optional ``tone``/``length``/
            ``draft_types`` are read.

    Returns:
        Partial state with the generated ``draft_bundle``, or an ``errors`` update
        if the provider call fails.
    """
    try:
        extracted = state.get("extracted_job")
        fit = state.get("fit_analysis")
        retrieved = state.get("retrieved_evidence") or []

        tone = state.get("tone") or Tone.WARM_PROFESSIONAL.value
        length = state.get("length") or DraftLength.MEDIUM.value
        draft_types = list(state.get("draft_types") or DEFAULT_DRAFT_TYPES)

        top_evidence = [
            {
                "evidence_chunk_id": attr(hit, "evidence_chunk_id"),
                "profile_item_id": attr(hit, "profile_item_id"),
                "title": attr(hit, "title"),
                "snippet": attr(hit, "snippet"),
                "source_type": attr(hit, "source_type"),
                # ``summary`` mirrors snippet so the deterministic fake provider
                # (which reads ``summary``) and real providers both stay grounded.
                "summary": attr(hit, "snippet"),
            }
            for hit in retrieved[:TOP_EVIDENCE_LIMIT]
        ]

        context = {
            "extracted_job": dump(extracted),
            "fit_summary": attr(fit, "summary", ""),
            "fit_score": attr(fit, "fit_score", 0),
            "positioning_strategy": attr(fit, "positioning_strategy", ""),
            "red_flags": attr(fit, "red_flags", []),
            "top_evidence": top_evidence,
            "tone": tone,
            "length": length,
            "draft_types": draft_types,
        }
        prompt = load_prompt("draft_bundle") + build_context_block(context)
        bundle = provider.structured(prompt, DraftBundle)
        return {"draft_bundle": bundle}
    except Exception as exc:
        return {
            "errors": append_error(
                state, "generate_draft_bundle", str(exc), type(exc).__name__
            )
        }
