"""``retrieve_evidence`` node — semantic search per requirement.

For every extracted requirement this node runs the ``evidence_search`` tool
(which delegates to :class:`~applypilot.services.profile_service.ProfileService`)
and turns the hits into:

* ``evidence_matches`` — :class:`~applypilot.schemas.evidence.EvidenceMatch`
  records linking a requirement to a specific profile evidence chunk, and
* ``retrieved_evidence`` — the de-duplicated
  :class:`~applypilot.schemas.profile.RetrievedEvidence` hits, reused later for
  draft grounding.

Vector search and re-ranking are *not* re-implemented here — they live in
``ProfileService`` so ingestion and retrieval share the same embedding model.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from applypilot.agents.nodes._common import append_error, clamp_unit
from applypilot.agents.state import ApplicationGraphState
from applypilot.agents.tools import evidence_search
from applypilot.schemas.evidence import EvidenceMatch
from applypilot.schemas.profile import RetrievedEvidence

#: Number of evidence chunks fetched per requirement before ranking.
EVIDENCE_TOP_K: int = 5
#: Minimum composite relevance score for a hit to count as evidence. Below this a
#: hit is search noise (the candidate has no genuine evidence for the requirement),
#: so the requirement is left unsupported and surfaces as a weak/missing match.
EVIDENCE_MIN_SCORE: float = 0.3
#: Maximum evidence chunks attached per requirement after thresholding.
EVIDENCE_MAX_PER_REQ: int = 3

#: Job-post boilerplate words that carry no skill signal. Stripped from a
#: requirement before searching so the query focuses on the actual technologies —
#: e.g. "Nice to have: Solidity / Web3 experience" → "Solidity Web3". Without this,
#: filler words dilute the relevance score and genuine matches fall below threshold.
_QUERY_NOISE: frozenset[str] = frozenset(
    {
        "required", "require", "requires", "must", "have", "has", "nice", "preferred",
        "plus", "bonus", "ability", "years", "year", "experience", "experienced",
        "strong", "proficient", "proficiency", "knowledge", "familiar", "familiarity",
        "expertise", "skilled", "skills", "skill", "working", "work", "solid", "deep",
        "extensive", "demonstrated", "proven", "hands", "handson", "to", "of", "with",
        "and", "or", "the", "a", "an", "in", "for", "at", "is", "are", "you", "we",
        "our", "your", "including", "such", "as", "etc", "ideally", "strongly", "good",
        "excellent", "minimum", "least", "across", "we're", "looking",
    }
)
_QUERY_WORD_RE = re.compile(r"[A-Za-z0-9.+#/]+")


def _search_query(requirement_text: str) -> str:
    """Reduce a requirement line to its skill-bearing tokens for search.

    Falls back to the original text when stripping leaves nothing meaningful.
    """
    kept = [
        token
        for token in _QUERY_WORD_RE.findall(requirement_text)
        if len(token.strip(".+#/")) > 1 and token.lower().strip(".+#/") not in _QUERY_NOISE
    ]
    return " ".join(kept) if kept else requirement_text


def retrieve_evidence(session: Session, state: ApplicationGraphState) -> dict[str, Any]:
    """Produce ``evidence_matches`` and ``retrieved_evidence`` for the requirements.

    Args:
        session: Injected SQLAlchemy session (bound by the graph factory).
        state: Current graph state; ``requirements`` is read.

    Returns:
        Partial state with ``evidence_matches`` (one per requirement/chunk hit)
        and the de-duplicated ``retrieved_evidence`` list, or an ``errors`` update
        if retrieval fails.
    """
    try:
        requirements = state.get("requirements") or []
        matches: list[EvidenceMatch] = []
        retrieved_by_chunk: dict[str, RetrievedEvidence] = {}

        for requirement in requirements:
            query = _search_query(requirement.text)
            hits = evidence_search(session, query, top_k=EVIDENCE_TOP_K)
            # Keep only genuinely relevant hits; unsupported requirements become gaps.
            relevant = [hit for hit in hits if hit.score >= EVIDENCE_MIN_SCORE][
                :EVIDENCE_MAX_PER_REQ
            ]
            for hit in relevant:
                matches.append(
                    EvidenceMatch(
                        requirement_id=requirement.id,
                        profile_item_id=hit.profile_item_id,
                        evidence_chunk_id=hit.evidence_chunk_id,
                        summary=hit.snippet,
                        confidence=clamp_unit(hit.score),
                    )
                )
                retrieved_by_chunk.setdefault(hit.evidence_chunk_id, hit)

        return {
            "evidence_matches": matches,
            "retrieved_evidence": list(retrieved_by_chunk.values()),
        }
    except Exception as exc:
        return {
            "errors": append_error(
                state, "retrieve_evidence", str(exc), type(exc).__name__
            )
        }
