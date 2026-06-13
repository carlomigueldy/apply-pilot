"""Shared LangGraph state for the application-analysis graph.

``ApplicationGraphState`` is the typed channel that flows through every node of
the application graph. ``application_id`` and ``raw_job_post`` are the required
inputs; every other key is produced by a downstream node and is therefore
optional (``total=False``).

The optional payload values are intentionally typed loosely (``Any`` /
``list[Any]``). At runtime they hold the corresponding Pydantic models defined in
``applypilot.schemas`` (``ExtractedJob``, ``JobRequirement``, ``EvidenceMatch``,
``FitAnalysis``, ``DraftBundle``, ``RetrievedEvidence``, ``GraphError``), but this
module deliberately does not import the schema layer to keep the agent state free
of import cycles and decoupled from the API surface.
"""

from __future__ import annotations

from typing import Any, TypedDict


class _ApplicationGraphInputs(TypedDict):
    """Required graph inputs, present from the very first node."""

    application_id: str
    raw_job_post: str


class ApplicationGraphState(_ApplicationGraphInputs, total=False):
    """Mutable state threaded through the application-analysis LangGraph.

    Required keys (inherited): ``application_id``, ``raw_job_post``.

    Optional keys (populated by the caller or by downstream nodes):
        user_id: Owning user id; used to load preferences (tone, salary, remote).
        extracted_job: Structured ``ExtractedJob`` parsed from the raw post.
        requirements: List of parsed ``JobRequirement`` items.
        evidence_matches: List of ``EvidenceMatch`` linking requirements to evidence.
        retrieved_evidence: List of ``RetrievedEvidence`` from semantic search.
        fit_analysis: The synthesized ``FitAnalysis``.
        draft_bundle: The generated ``DraftBundle`` of application content.
        review_decision: The recorded human-in-the-loop review decision.
        tone: Draft tone (a :class:`~applypilot.schemas.enums.Tone` value); may be
            supplied by the caller or derived from user preferences mid-graph.
        length: Draft length (a :class:`~applypilot.schemas.enums.DraftLength` value).
        draft_types: Optional allowlist of draft types to generate; defaults to all.
        persisted_ids: Ids of the rows written by ``persist_outputs`` (observability).
        errors: List of ``GraphError`` accumulated across nodes.
    """

    user_id: str
    extracted_job: Any
    requirements: list[Any]
    evidence_matches: list[Any]
    retrieved_evidence: list[Any]
    fit_analysis: Any
    draft_bundle: Any
    review_decision: Any
    tone: str
    length: str
    draft_types: list[str]
    persisted_ids: dict[str, Any]
    errors: list[Any]
