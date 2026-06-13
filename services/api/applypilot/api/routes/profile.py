"""Profile item routes.

Exposes CRUD endpoints for :class:`ProfileItem` records and the semantic
search endpoint that queries the user's evidence knowledge-base.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from applypilot.api.deps import SessionDep
from applypilot.schemas.profile import (
    ProfileItemCreate,
    ProfileItemRead,
    ProfileItemUpdate,
    ProfileSearchRequest,
    ProfileSearchResponse,
)
from applypilot.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])

# Annotated aliases keep FastAPI Query metadata while satisfying ruff B008.
OptionalUserIdQuery = Annotated[
    uuid.UUID | None,
    Query(description="Filter by user ID"),
]
RequiredUserIdQuery = Annotated[
    uuid.UUID,
    Query(description="Owner user ID"),
]


@router.get("/items", response_model=list[ProfileItemRead])
def list_items(
    session: SessionDep,
    user_id: OptionalUserIdQuery = None,
) -> list[ProfileItemRead]:
    """List all profile items, optionally filtered to a single user."""
    return ProfileService(session).list_items(user_id=user_id)


@router.post("/items", response_model=ProfileItemRead, status_code=201)
def create_item(
    data: ProfileItemCreate,
    session: SessionDep,
    user_id: RequiredUserIdQuery,
) -> ProfileItemRead:
    """Create a profile item and persist its embedded evidence chunks."""
    return ProfileService(session).create_item(user_id=user_id, data=data)


@router.patch("/items/{item_id}", response_model=ProfileItemRead)
def update_item(
    item_id: uuid.UUID,
    data: ProfileItemUpdate,
    session: SessionDep,
) -> ProfileItemRead:
    """Partially update a profile item; re-embeds chunks when body changes."""
    try:
        return ProfileService(session).update_item(item_id=item_id, data=data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: uuid.UUID,
    session: SessionDep,
) -> None:
    """Delete a profile item and its evidence chunks."""
    try:
        ProfileService(session).delete_item(item_id=item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/items/{item_id}/regenerate-embeddings", response_model=ProfileItemRead)
def regenerate_embeddings(
    item_id: uuid.UUID,
    session: SessionDep,
) -> ProfileItemRead:
    """Delete and re-create all evidence chunks for the given profile item."""
    try:
        return ProfileService(session).regenerate_embeddings(item_id=item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/search", response_model=ProfileSearchResponse)
def search_profile(
    request: ProfileSearchRequest,
    session: SessionDep,
) -> ProfileSearchResponse:
    """Semantically search a user's profile evidence knowledge-base."""
    return ProfileService(session).search(request)
