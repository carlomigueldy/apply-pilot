"""Profile-domain repositories: ProfileItem and EvidenceChunk."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Float, cast, or_, select, type_coerce
from sqlalchemy.orm import Session

from applypilot.db.models import EvidenceChunk, ProfileItem


class ProfileItemRepository:
    """CRUD operations for :class:`~applypilot.db.models.ProfileItem`."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: uuid.UUID,
        type: str,  # noqa: A002
        title: str,
        body: str,
        item_metadata: dict[str, Any] | None = None,
    ) -> ProfileItem:
        """Persist a new profile item and flush to assign a DB-generated id."""
        item = ProfileItem(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            item_metadata=item_metadata or {},
        )
        self.session.add(item)
        self.session.flush()
        return item

    def get(self, profile_item_id: uuid.UUID) -> ProfileItem | None:
        """Return the profile item with *profile_item_id*, or ``None``."""
        stmt = select(ProfileItem).where(ProfileItem.id == profile_item_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: uuid.UUID) -> Sequence[ProfileItem]:
        """Return all profile items belonging to *user_id*."""
        stmt = select(ProfileItem).where(ProfileItem.user_id == user_id)
        return self.session.execute(stmt).scalars().all()

    def update(
        self, profile_item_id: uuid.UUID, **kwargs: Any
    ) -> ProfileItem | None:
        """Apply *kwargs* as attribute updates; return the updated item or ``None``."""
        item = self.get(profile_item_id)
        if item is None:
            return None
        for key, value in kwargs.items():
            setattr(item, key, value)
        self.session.flush()
        return item

    def delete(self, profile_item_id: uuid.UUID) -> bool:
        """Delete the profile item; return ``True`` if it existed."""
        item = self.get(profile_item_id)
        if item is None:
            return False
        self.session.delete(item)
        self.session.flush()
        return True

    def list_evidence_chunks(self, profile_item_id: uuid.UUID) -> Sequence[EvidenceChunk]:
        """Return all evidence chunks for a profile item, ordered by chunk_index."""
        stmt = (
            select(EvidenceChunk)
            .where(EvidenceChunk.profile_item_id == profile_item_id)
            .order_by(EvidenceChunk.chunk_index)
        )
        return self.session.execute(stmt).scalars().all()


class EvidenceChunkRepository:
    """Canonical repository for :class:`~applypilot.db.models.EvidenceChunk`.

    This is intentionally **stateless** — every method accepts an explicit
    :class:`~sqlalchemy.orm.Session` so that callers decide the transaction
    boundary.  Two retrieval strategies are supported:

    * **Vector search** — pgvector cosine distance via the ``<=>`` operator,
      returning ``(EvidenceChunk, similarity)`` pairs where similarity ∈ [0, 1].
    * **Keyword search** — ``ILIKE`` match on ``chunk_text`` for exact tech tokens.
    """

    def bulk_create(
        self, session: Session, chunks: list[dict[str, Any]]
    ) -> list[EvidenceChunk]:
        """Persist a batch of chunks from a list of attribute dicts.

        Dict keys must use Python attribute names (``chunk_metadata``, not
        ``metadata``).
        """
        objects = [EvidenceChunk(**chunk) for chunk in chunks]
        session.add_all(objects)
        session.flush()
        return objects

    def vector_search(
        self,
        session: Session,
        query_embedding: list[float],
        top_k: int,
        profile_item_ids: list[uuid.UUID] | None = None,
    ) -> list[tuple[EvidenceChunk, float]]:
        """Return up to *top_k* chunks ranked by cosine similarity.

        Args:
            session: Active SQLAlchemy session.
            query_embedding: 1536-dim query vector.
            top_k: Maximum number of results to return.
            profile_item_ids: When provided, restricts search to these items.

        Returns:
            List of ``(EvidenceChunk, similarity_score)`` tuples where
            *similarity_score* is in [0, 1] (1 = identical direction,
            0 = orthogonal).  pgvector cosine distance ∈ [0, 2] is converted
            to similarity via ``max(0.0, 1.0 - distance)``.
        """
        from pgvector.sqlalchemy import Vector

        distance_expr = type_coerce(
            EvidenceChunk.embedding.op("<=>")(cast(query_embedding, Vector(1536))),
            Float(),
        )
        stmt = (
            select(EvidenceChunk, distance_expr.label("_dist"))
            .where(EvidenceChunk.embedding.isnot(None))
            .order_by(distance_expr)
            .limit(top_k)
        )
        if profile_item_ids is not None:
            stmt = stmt.where(EvidenceChunk.profile_item_id.in_(profile_item_ids))

        rows = session.execute(stmt).all()
        return [(row[0], max(0.0, 1.0 - float(row[1]))) for row in rows]

    def keyword_search(
        self, session: Session, tokens: list[str]
    ) -> Sequence[EvidenceChunk]:
        """Return chunks whose ``chunk_text`` matches any token via ``ILIKE``.

        Returns an empty list immediately when *tokens* is empty.
        """
        if not tokens:
            return []
        conditions = [
            EvidenceChunk.chunk_text.ilike(f"%{token}%") for token in tokens
        ]
        stmt = select(EvidenceChunk).where(or_(*conditions))
        return session.execute(stmt).scalars().all()
