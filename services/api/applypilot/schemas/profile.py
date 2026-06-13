"""Schemas for profile items and profile semantic search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from applypilot.schemas.common import ORMModel, TimestampedSchema
from applypilot.schemas.enums import ProfileItemType


class ProfileItemBase(BaseModel):
    """Shared fields for a profile item."""

    type: ProfileItemType
    title: str
    body: str
    item_metadata: dict[str, Any] | None = None


class ProfileItemCreate(ProfileItemBase):
    """Payload to create a profile item."""


class ProfileItemUpdate(BaseModel):
    """Payload to partially update a profile item; all fields optional."""

    type: ProfileItemType | None = None
    title: str | None = None
    body: str | None = None
    item_metadata: dict[str, Any] | None = None


class ProfileItemRead(ORMModel, TimestampedSchema):
    """Profile item as returned from the API."""

    id: UUID
    user_id: UUID
    type: ProfileItemType
    title: str
    body: str
    item_metadata: dict[str, Any] | None = None


class ProfileSearchRequest(BaseModel):
    """Request to semantically search a user's profile evidence."""

    query: str
    top_k: int = 8
    types: list[ProfileItemType] | None = None


class RetrievedEvidence(BaseModel):
    """A single retrieved evidence chunk from a profile search."""

    evidence_chunk_id: str
    profile_item_id: str
    title: str
    snippet: str
    score: float
    source_type: str


class ProfileSearchResponse(BaseModel):
    """Response wrapping ranked profile search results."""

    results: list[RetrievedEvidence]
