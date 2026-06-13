"""Schemas for matching profile evidence against job requirements."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceMatch(BaseModel):
    """A match between a job requirement and a piece of profile evidence."""

    requirement_id: str
    profile_item_id: str
    evidence_chunk_id: str
    summary: str
    confidence: float = Field(ge=0, le=1)


class EvidenceMatchList(BaseModel):
    """Structured list of evidence matches."""

    matches: list[EvidenceMatch]
