"""evidence_search tool — semantic search over the user's profile evidence.

A thin synchronous wrapper around
:class:`~applypilot.services.profile_service.ProfileService` that translates
raw parameters into a :class:`~applypilot.schemas.profile.ProfileSearchRequest`
and returns a list of :class:`~applypilot.schemas.profile.RetrievedEvidence`
items. Embedding generation, candidate pooling, and composite re-ranking are
handled entirely by :class:`~applypilot.services.profile_service.ProfileService`
so that the same logic is used at ingestion *and* retrieval time.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from applypilot.schemas.enums import ProfileItemType
from applypilot.schemas.profile import ProfileSearchRequest, RetrievedEvidence
from applypilot.services.profile_service import ProfileService


def evidence_search(
    session: Session,
    query: str,
    top_k: int = 8,
    types: list[ProfileItemType] | None = None,
) -> list[RetrievedEvidence]:
    """Return profile evidence chunks most relevant to *query*.

    Delegates entirely to
    :meth:`~applypilot.services.profile_service.ProfileService.search` so the
    same embedding model and re-ranking weights used during ingestion are applied
    at retrieval time — a prerequisite for meaningful cosine similarity scores.

    Args:
        session: Active SQLAlchemy session (sync, not async).
        query: Natural-language search query, typically a job requirement text
            (e.g. ``"3+ years experience with Python FastAPI"``).
        top_k: Maximum number of evidence chunks to return.  Defaults to ``8``.
        types: Optional allowlist of
            :class:`~applypilot.schemas.enums.ProfileItemType` values to
            restrict the search scope (e.g. ``[ProfileItemType.ROLE]``).
            When ``None``, all item types are considered.

    Returns:
        Ranked list of :class:`~applypilot.schemas.profile.RetrievedEvidence`
        items, most relevant first.  The list is empty when no evidence exists
        or nothing passes the re-ranking threshold.
    """
    request = ProfileSearchRequest(query=query, top_k=top_k, types=types)
    response = ProfileService(session).search(request)
    return response.results
