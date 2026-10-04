"""Club and membership schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.sport_fields import is_known_sport, resolve_club_sport
from app.models.enums import ActivityCategory, SportCategory, UserRole
from app.schemas.common import ORMModel


def _resolve_sport(sport_slug: str) -> tuple[SportCategory, ActivityCategory]:
    """Validate a club's sport slug and derive its category fields.

    Raises :class:`ValueError` (-> HTTP 422) for an unknown slug. RALLY is
    sports-only, so a club's sport must come from the sports catalog.
    """
    if not is_known_sport(sport_slug):
        raise ValueError(f"Unknown sport slug {sport_slug!r}")
    resolved = resolve_club_sport(sport_slug)
    return SportCategory(resolved["sport_category"]), ActivityCategory(resolved["category"])


class ClubBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(
        min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$"
    )
    description: str | None = Field(default=None, max_length=8000)
    category: ActivityCategory | None = None
    #: SPORT slug from :mod:`app.core.sports` (e.g. padel, running).
    sport_slug: str | None = Field(default=None, max_length=40)
    #: Derived from ``sport_slug`` - never required from the client.
    sport_category: SportCategory | None = None
    city: str | None = Field(default=None, max_length=120)
    is_public: bool = True

    @model_validator(mode="after")
    def _bind_sport(self) -> "ClubBase":
        """Bind the club to a known sport and derive its category fields."""
        if self.sport_slug is not None:
            sport_category, category = _resolve_sport(self.sport_slug)
            self.sport_category = sport_category
            if self.category is None:
                self.category = category
        if self.category is None:
            raise ValueError("category is required when no sport_slug is provided")
        return self


class ClubCreate(ClubBase):
    """Create a club; the caller becomes its owner and first member."""


class ClubUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=8000)
    category: ActivityCategory | None = None
    sport_slug: str | None = Field(default=None, max_length=40)
    sport_category: SportCategory | None = None
    city: str | None = Field(default=None, max_length=120)
    is_public: bool | None = None

    @model_validator(mode="after")
    def _bind_sport(self) -> "ClubUpdate":
        """Validate a changed sport slug and keep category fields consistent."""
        if self.sport_slug is not None:
            sport_category, category = _resolve_sport(self.sport_slug)
            self.sport_category = sport_category
            if self.category is None:
                self.category = category
        return self


class ClubMemberRead(ORMModel):
    id: uuid.UUID
    club_id: uuid.UUID
    user_id: uuid.UUID
    role: UserRole
    is_active: bool
    joined_at: datetime | None = None


class ClubRead(ORMModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    category: ActivityCategory
    sport_slug: str | None = None
    sport_category: SportCategory | None = None
    city: str | None = None
    is_public: bool
    created_at: datetime
    member_count: int = 0
