"""profile_lookup tool — retrieve individual or type-grouped profile items.

Provides two complementary access patterns:

* :func:`profile_lookup` — fetch a single item by its UUID.
* :func:`list_profile_by_type` — fetch all items that belong to a given
  :class:`~applypilot.schemas.enums.ProfileItemType` category.

Both functions are synchronous and reuse the SQLAlchemy ``Session`` passed by
the calling node; no new sessions are created here.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from applypilot.db.models import ProfileItem
from applypilot.schemas.enums import ProfileItemType
from applypilot.schemas.profile import ProfileItemRead
from applypilot.services.profile_service import ProfileService


def profile_lookup(session: Session, item_id: uuid.UUID | str) -> ProfileItemRead:
    """Return a single :class:`~applypilot.schemas.profile.ProfileItemRead` by *item_id*.

    Delegates to :meth:`~applypilot.services.profile_service.ProfileService.get_item`
    so the result is always a fully-validated Pydantic model.

    Args:
        session: Active SQLAlchemy session.
        item_id: UUID of the profile item to retrieve.  May be supplied as a
            :class:`uuid.UUID` instance or a UUID string.

    Returns:
        The matching :class:`~applypilot.schemas.profile.ProfileItemRead`.

    Raises:
        ValueError: When no item with *item_id* exists in the database.
        ValueError: When *item_id* is a string that cannot be parsed as a UUID.
    """
    resolved: uuid.UUID = uuid.UUID(item_id) if isinstance(item_id, str) else item_id
    return ProfileService(session).get_item(resolved)


def list_profile_by_type(
    session: Session,
    type: ProfileItemType | str,  # noqa: A002
) -> list[ProfileItemRead]:
    """Return all profile items that belong to *type*.

    Uses a direct SQLAlchemy query filtered on the ``type`` text column so the
    operation is a single round-trip to the database.  Results are returned in
    database insertion order.

    Args:
        session: Active SQLAlchemy session.
        type: :class:`~applypilot.schemas.enums.ProfileItemType` value (or its
            equivalent string, e.g. ``"role"``) to filter on.

    Returns:
        List of :class:`~applypilot.schemas.profile.ProfileItemRead` items whose
        ``type`` column matches.  Returns an empty list when none are found.
    """
    type_value: str = type.value if isinstance(type, ProfileItemType) else str(type)
    stmt = select(ProfileItem).where(ProfileItem.type == type_value)
    items = session.execute(stmt).scalars().all()
    return [ProfileItemRead.model_validate(item) for item in items]
