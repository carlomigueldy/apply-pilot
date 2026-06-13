"""Common Pydantic base classes and mixins for ApplyPilot schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema for models read from ORM objects.

    Enables ``from_attributes`` so SQLAlchemy instances can be validated
    directly into Pydantic models.
    """

    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(BaseModel):
    """Mixin providing ``created_at`` / ``updated_at`` timestamp fields."""

    created_at: datetime
    updated_at: datetime
