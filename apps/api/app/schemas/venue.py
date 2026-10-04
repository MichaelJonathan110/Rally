"""Venue, court and availability schemas."""
from __future__ import annotations

import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ActivityCategory
from app.schemas.common import ORMModel


class VenueAvailabilityBase(BaseModel):
    """A recurring weekly opening window (0=Monday .. 6=Sunday)."""

    weekday: int = Field(ge=0, le=6)
    opens_at: time
    closes_at: time
    is_active: bool = True

    @model_validator(mode="after")
    def _check_window(self) -> "VenueAvailabilityBase":
        if self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be after opens_at")
        return self


class VenueAvailabilityRead(ORMModel):
    id: uuid.UUID
    weekday: int
    opens_at: time
    closes_at: time
    is_active: bool


class VenueCourtBase(BaseModel):
    """A bookable resource (VenueCourt) typed by venue_kind (app.core.sports)."""

    name: str = Field(min_length=1, max_length=80)
    surface: str | None = Field(default=None, max_length=60)
    capacity: int = Field(default=1, ge=1, le=10000)
    hourly_price_cents: int = Field(default=0, ge=0, le=10_000_000)
    is_active: bool = True
    #: venue_kind of the sport this resource serves (e.g. "court", "field").
    venue_kind: str | None = Field(default=None, max_length=40)
    #: Human label of the resource (sports-catalog resource_label, e.g. "Court").
    resource_label: str | None = Field(default=None, max_length=60)


class VenueCourtCreate(VenueCourtBase):
    availability: list[VenueAvailabilityBase] = Field(default_factory=list)


class VenueCourtRead(ORMModel):
    id: uuid.UUID
    venue_id: uuid.UUID
    name: str
    surface: str | None = None
    capacity: int
    hourly_price_cents: int
    is_active: bool
    venue_kind: str | None = None
    resource_label: str | None = None
    availability: list[VenueAvailabilityRead] = Field(default_factory=list)


class VenueResourceRead(BaseModel):
    """A bookable resource on the venue payload: kind + label + its own windows."""

    id: uuid.UUID
    name: str
    kind: str | None = None
    label: str | None = None
    availability: list[VenueAvailabilityRead] = Field(default_factory=list)


class VenueAvailabilitySummary(BaseModel):
    """Per-resource availability roll-up (never a single venue-level blob)."""

    resource_count: int = 0
    resources_with_windows: int = 0
    total_windows: int = 0
    open_weekdays: list[int] = Field(default_factory=list)
    earliest_open: time | None = None
    latest_close: time | None = None


class VenueBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=8000)
    address_line: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=120)
    province: str | None = Field(default=None, max_length=80)
    area: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    category: ActivityCategory | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str = Field(default="UTC", max_length=64)
    is_active: bool = True
    #: Primary resource kind this venue provides (venue_kind from sports.py).
    venue_kind: str | None = Field(default=None, max_length=40)
    #: Sport slugs (app.core.sports) this venue supports.
    sport_slugs: list[str] = Field(default_factory=list)


class VenueCreate(VenueBase):
    """Create a venue, optionally with its resources (courts) in one call."""

    courts: list[VenueCourtCreate] = Field(default_factory=list)


class VenueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=8000)
    address_line: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    province: str | None = Field(default=None, max_length=80)
    area: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    category: ActivityCategory | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None
    venue_kind: str | None = Field(default=None, max_length=40)
    sport_slugs: list[str] | None = None


class VenueRead(ORMModel):
    id: uuid.UUID
    owner_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    address_line: str | None = None
    city: str
    province: str | None = None
    area: str | None = None
    country: str | None = None
    category: ActivityCategory | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str
    is_active: bool
    created_at: datetime
    #: Secondary location line shown under the primary name (e.g. "Tangerang, Indonesia").
    location: str | None = None
    #: Primary resource kind (venue_kind) this venue serves.
    venue_kind: str | None = None
    #: Sport slugs (app.core.sports) this venue supports.
    sport_slugs: list[str] = Field(default_factory=list)
    #: Bookable resources (VenueCourt rows) typed by venue_kind.
    resources: list[VenueResourceRead] = Field(default_factory=list)
    #: Per-resource availability roll-up for the venue.
    availability: VenueAvailabilitySummary = Field(default_factory=VenueAvailabilitySummary)
    court_count: int = 0
