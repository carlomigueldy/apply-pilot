"""Schemas for generated drafts and draft review operations."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from applypilot.schemas.common import ORMModel, TimestampedSchema
from applypilot.schemas.enums import DraftLength, DraftStatus, DraftType, Tone


class DraftItem(BaseModel):
    """A single generated draft within a bundle."""

    type: DraftType
    title: str
    body: str


class DraftBundle(BaseModel):
    """Structured bundle of generated drafts."""

    drafts: list[DraftItem]


class DraftRead(ORMModel, TimestampedSchema):
    """A persisted draft as returned from the API."""

    id: UUID
    application_id: UUID
    type: DraftType
    title: str
    body: str
    status: DraftStatus
    version: int
    tone: Tone | None = None
    length: DraftLength | None = None
    review_notes: str | None = None


class DraftApproveRequest(BaseModel):
    """Payload to approve (and optionally edit) a draft."""

    draft_id: str
    edited_body: str | None = None
    notes: str | None = None


class RegenerateSectionRequest(BaseModel):
    """Payload to regenerate a single draft section."""

    type: DraftType
    tone: Tone | None = None
    length: DraftLength | None = None
    instructions: str | None = None
