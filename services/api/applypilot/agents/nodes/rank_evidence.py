"""``rank_evidence`` node — de-duplicate and trim evidence per requirement.

Retrieval can surface the same chunk for a requirement more than once and more
hits than are useful for grounding. This node keeps the output deterministic and
focused: it drops duplicate ``(requirement_id, evidence_chunk_id)`` pairs and
keeps only the highest-confidence matches per requirement. No I/O, no LLM.
"""

from __future__ import annotations

from typing import Any

from applypilot.agents.state import ApplicationGraphState
from applypilot.schemas.evidence import EvidenceMatch

#: Maximum evidence matches retained per requirement after ranking.
TOP_MATCHES_PER_REQUIREMENT: int = 3


def rank_evidence(state: ApplicationGraphState) -> dict[str, Any]:
    """Return ``{'evidence_matches': [...]}`` de-duplicated, ranked, and trimmed.

    Ordering is stable and deterministic: requirements keep their first-seen
    order, and within each requirement matches are sorted by descending
    confidence (Python's stable sort preserves retrieval order on ties).
    """
    matches: list[EvidenceMatch] = list(state.get("evidence_matches") or [])

    seen: set[tuple[str, str]] = set()
    by_requirement: dict[str, list[EvidenceMatch]] = {}
    for match in matches:
        key = (match.requirement_id, match.evidence_chunk_id)
        if key in seen:
            continue
        seen.add(key)
        by_requirement.setdefault(match.requirement_id, []).append(match)

    ranked: list[EvidenceMatch] = []
    for requirement_matches in by_requirement.values():
        requirement_matches.sort(key=lambda m: m.confidence, reverse=True)
        ranked.extend(requirement_matches[:TOP_MATCHES_PER_REQUIREMENT])

    return {"evidence_matches": ranked}
