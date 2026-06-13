"""Profile knowledge-base service.

Owns the create/read/update/delete lifecycle for :class:`ProfileItem` records
and their associated :class:`EvidenceChunk` embeddings. Implements semantic
search using pgvector cosine distance with a keyword-token fallback, followed
by weighted re-ranking.

Embedding generation is delegated to the single canonical provider returned by
:func:`applypilot.agents.llm.factory.get_embedding_provider`, and chunking to
:class:`applypilot.services.embedding_service.EmbeddingService`, so that seed,
ingestion, and search all embed text with the *same* function — a prerequisite
for cosine similarity to be meaningful across stored chunks and live queries.

All operations are synchronous per the ApplyPilot backend convention.
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from applypilot.agents.llm.base import EmbeddingProvider
from applypilot.agents.llm.factory import get_embedding_provider
from applypilot.core.config import get_settings
from applypilot.db.models import EvidenceChunk, ProfileItem
from applypilot.db.repositories.profile_repository import EvidenceChunkRepository
from applypilot.schemas.profile import (
    ProfileItemCreate,
    ProfileItemRead,
    ProfileItemUpdate,
    ProfileSearchRequest,
    ProfileSearchResponse,
    RetrievedEvidence,
)
from applypilot.services.embedding_service import EmbeddingService

# ---------------------------------------------------------------------------
# Re-ranking weights
# ---------------------------------------------------------------------------
#
# Final relevance = W_VECTOR * cosine_similarity
#                 + W_COVERAGE * (distinct query tokens found in chunk/title)
#                 + W_TITLE * (distinct query tokens found in the item title)
#
# The crude deterministic fake embedding dilutes a chunk's signal across all its
# tokens, so cosine alone ranks compact generic chunks above focused-but-verbose
# evidence. Query-token coverage and (especially) the item title — the least
# diluted, most topical signal — make the dedicated evidence win. These weights
# are also sensible for real embedding providers, where cosine carries more.

_W_VECTOR: float = 0.3
_W_COVERAGE: float = 0.3
_W_TITLE: float = 0.4

_TOKEN_RE = re.compile(r"[a-z0-9]+")
#: Function words ignored when deriving query tokens for lexical scoring.
_QUERY_STOPWORDS: frozenset[str] = frozenset(
    {"and", "or", "the", "a", "an", "of", "to", "in", "on", "for", "with", "at", "by", "from"}
)


def _significant_tokens(value: str) -> set[str]:
    """Lower-case, tokenise on ``[a-z0-9]+``, drop 1-char and function words."""
    return {
        t
        for t in _TOKEN_RE.findall(value.lower())
        if len(t) > 1 and t not in _QUERY_STOPWORDS
    }


# ---------------------------------------------------------------------------
# Profile service
# ---------------------------------------------------------------------------


class ProfileService:
    """Domain service for profile items and evidence-chunk search."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._settings = get_settings()
        self._provider: EmbeddingProvider = get_embedding_provider(self._settings)
        self._embedding_svc = EmbeddingService(self._provider)
        self._chunk_repo = EvidenceChunkRepository()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed_and_persist_chunks(self, item: ProfileItem, body: str) -> None:
        """Chunk *body*, embed each chunk, and persist :class:`EvidenceChunk` rows."""
        chunks = self._embedding_svc.chunk_text(body)
        for idx, chunk_text in enumerate(chunks):
            embedding = self._provider.embed_text(chunk_text)
            self._session.add(
                EvidenceChunk(
                    profile_item_id=item.id,
                    chunk_text=chunk_text,
                    chunk_index=idx,
                    embedding=embedding,
                    chunk_metadata={},
                )
            )

    def _delete_chunks(self, item: ProfileItem) -> None:
        """Delete all evidence chunks attached to *item*."""
        for chunk in list(item.evidence_chunks):
            self._session.delete(chunk)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_item(self, user_id: uuid.UUID, data: ProfileItemCreate) -> ProfileItemRead:
        """Persist a new profile item and its embedded evidence chunks."""
        item = ProfileItem(
            user_id=user_id,
            type=data.type.value,
            title=data.title,
            body=data.body,
            item_metadata=data.item_metadata or {},
        )
        self._session.add(item)
        self._session.flush()  # obtain item.id before embedding
        self._embed_and_persist_chunks(item, data.body)
        self._session.commit()
        return ProfileItemRead.model_validate(item)

    def get_item(self, item_id: uuid.UUID) -> ProfileItemRead:
        """Return a single profile item or raise :exc:`ValueError`."""
        item = self._session.get(ProfileItem, item_id)
        if item is None:
            raise ValueError(f"ProfileItem {item_id} not found")
        return ProfileItemRead.model_validate(item)

    def list_items(self, user_id: uuid.UUID | None = None) -> list[ProfileItemRead]:
        """Return all profile items, optionally filtered by *user_id*."""
        stmt = select(ProfileItem)
        if user_id is not None:
            stmt = stmt.where(ProfileItem.user_id == user_id)
        items = self._session.execute(stmt).scalars().all()
        return [ProfileItemRead.model_validate(item) for item in items]

    def update_item(self, item_id: uuid.UUID, data: ProfileItemUpdate) -> ProfileItemRead:
        """Apply a partial update to a profile item; re-embeds if body changed."""
        item = self._session.get(ProfileItem, item_id)
        if item is None:
            raise ValueError(f"ProfileItem {item_id} not found")

        if data.type is not None:
            item.type = data.type.value
        if data.title is not None:
            item.title = data.title
        if data.item_metadata is not None:
            item.item_metadata = data.item_metadata

        if data.body is not None:
            item.body = data.body
            self._delete_chunks(item)
            self._session.flush()
            self._embed_and_persist_chunks(item, item.body)

        self._session.commit()
        return ProfileItemRead.model_validate(item)

    def delete_item(self, item_id: uuid.UUID) -> None:
        """Delete a profile item and all its evidence chunks (cascade)."""
        item = self._session.get(ProfileItem, item_id)
        if item is None:
            raise ValueError(f"ProfileItem {item_id} not found")
        self._session.delete(item)
        self._session.commit()

    def regenerate_embeddings(self, item_id: uuid.UUID) -> ProfileItemRead:
        """Delete and re-create all evidence chunks for *item_id*."""
        item = self._session.get(ProfileItem, item_id)
        if item is None:
            raise ValueError(f"ProfileItem {item_id} not found")
        self._delete_chunks(item)
        self._session.flush()
        self._embed_and_persist_chunks(item, item.body)
        self._session.commit()
        return ProfileItemRead.model_validate(item)

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    def search(self, request: ProfileSearchRequest) -> ProfileSearchResponse:
        """Retrieve and rank evidence chunks relevant to *request.query*.

        Strategy:
        1. Build a candidate pool: pgvector cosine top-N ∪ chunks whose text
           contains any significant query token (keyword fallback).
        2. Score every candidate with a composite of cosine similarity,
           query-token coverage, and item-title match (see the weight constants).
        3. Re-rank by composite score and return the top-``top_k``
           :class:`RetrievedEvidence` items.
        """
        query_tokens = _significant_tokens(request.query)
        query_embedding = self._provider.embed_text(request.query)
        token_count = len(query_tokens) or 1

        # Resolve type filter → profile_item_ids
        item_ids: list[uuid.UUID] | None = None
        if request.types:
            type_values = [t.value for t in request.types]
            filtered_items = (
                self._session.execute(
                    select(ProfileItem).where(ProfileItem.type.in_(type_values))
                )
                .scalars()
                .all()
            )
            item_ids = [it.id for it in filtered_items]
            if not item_ids:
                return ProfileSearchResponse(results=[])

        # 1a. Vector candidates (wide net so re-ranking has room to work)
        candidate_n = max(request.top_k * 4, 20)
        vector_results = self._chunk_repo.vector_search(
            self._session, query_embedding, candidate_n, item_ids
        )
        vec_sim: dict[uuid.UUID, float] = {c.id: s for c, s in vector_results}
        candidates: dict[uuid.UUID, EvidenceChunk] = {c.id: c for c, _ in vector_results}

        # 1b. Keyword candidates — chunks containing any significant query token
        if query_tokens:
            kw_stmt = select(EvidenceChunk).where(
                or_(*[EvidenceChunk.chunk_text.ilike(f"%{t}%") for t in query_tokens])
            )
            if item_ids is not None:
                kw_stmt = kw_stmt.where(EvidenceChunk.profile_item_id.in_(item_ids))
            for chunk in self._session.execute(kw_stmt).scalars().all():
                candidates.setdefault(chunk.id, chunk)

        if not candidates:
            return ProfileSearchResponse(results=[])

        # Load parent profile items for title scoring + metadata
        parent_ids = {c.profile_item_id for c in candidates.values()}
        items_by_id = {
            it.id: it
            for it in self._session.execute(
                select(ProfileItem).where(ProfileItem.id.in_(parent_ids))
            )
            .scalars()
            .all()
        }

        # 2. Composite scoring
        scored: list[tuple[EvidenceChunk, ProfileItem, float]] = []
        for cid, chunk in candidates.items():
            parent = items_by_id.get(chunk.profile_item_id)
            if parent is None:
                continue
            body_tokens = _significant_tokens(chunk.chunk_text or "")
            title_tokens = _significant_tokens(parent.title or "")
            coverage = len(query_tokens & (body_tokens | title_tokens)) / token_count
            title_match = len(query_tokens & title_tokens) / token_count
            score = (
                _W_VECTOR * vec_sim.get(cid, 0.0)
                + _W_COVERAGE * coverage
                + _W_TITLE * title_match
            )
            scored.append((chunk, parent, score))

        # 3. Re-rank and trim
        scored.sort(key=lambda t: t[2], reverse=True)
        top = scored[: request.top_k]

        results = [
            RetrievedEvidence(
                evidence_chunk_id=str(chunk.id),
                profile_item_id=str(chunk.profile_item_id),
                title=parent.title,
                snippet=chunk.chunk_text[:200],
                score=round(score, 4),
                source_type=parent.type,
            )
            for chunk, parent, score in top
        ]
        return ProfileSearchResponse(results=results)
