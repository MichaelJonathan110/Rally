"""Activity request/response schemas.

Activities are the core domain object. RALLY is sports-only, so an activity is
defined by its sport (a slug from :mod:`app.core.sports`): the sport's catalog
row drives the allowed variants/formats and the default tracked metrics. The
legacy generic ``category``/``activity_type`` fields are kept for backward
compatibility, but the sport category (racket/team/combat/...) is what new
activities are categorised by.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.core.sport_fields import (
    SportFieldError,
    activity_category_for_sport,
    resolve_sport_fields,
)
from app.models.enums import (
    ActivityCategory,
    ActivityVisibility,
    ParticipantStatus,
    SkillLevel,
    SportCategory,
)
from app.schemas.common import ORMModel


class ActivityCategoryLinkCreate(BaseModel):
    """Admin-managed config row for the activity engine."""

    slug: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=2, max_length=80)
    category: ActivityCategory
    description: str | None = Field(default=None, max_length=2000)
    icon: str | None = Field(default=None, max_length=60)
    sort_order: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True


class ActivityCategoryLinkRead(ORMModel):
    id: uuid.UUID
    slug: str
    name: str
    category: ActivityCategory
    description: str | None = None
    icon: str | None = None
    sort_order: int
    is_active: bool


class VenueBrief(ORMModel):
    """Minimal venue info embedded in an activity (name + location)."""

    id: uuid.UUID
    name: str
    city: str
    province: str | None = None
    area: str | None = None


class ActivityBase(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    #: SPORT slug from the sports catalog (e.g. padel, tennis, football).
    sport_slug: str | None = Field(default=None, max_length=40)
    #: Variant within the sport (must be one of the sport's catalog variants).
    sport_variant: str | None = Field(default=None, max_length=40)
    #: Format within the sport (must be one of the sport's catalog formats).
    sport_format: str | None = Field(default=None, max_length=40)
    #: Metrics tracked for this activity (subset of the sport's catalog metrics).
    sport_metrics: list[str] | None = None
    #: Legacy generic type (kept for backward compatibility with old clients).
    activity_type: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=8000)
    #: Legacy high-level category; derived from the sport when omitted.
    category: ActivityCategory | None = None
    #: Sport category (racket/team/combat/...); derived from ``sport_slug``.
    sport_category: SportCategory | None = None
    skill_level: SkillLevel = SkillLevel.ANY
    visibility: ActivityVisibility = ActivityVisibility.PUBLIC
    venue_id: uuid.UUID | None = None
    #: The specific bookable resource at the venue (Phase 2 sport-aware court).
    venue_court_id: uuid.UUID | None = None
    club_id: uuid.UUID | None = None
    category_link_id: uuid.UUID | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    max_participants: int = Field(default=10, ge=1, le=1000)
    cost_per_person_cents: int = Field(default=0, ge=0, le=10_000_000)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @model_validator(mode="after")
    def _check_sport(self) -> "ActivityBase":
        """Validate sport-specific fields and derive the sport category."""
        try:
            resolved = resolve_sport_fields(
                sport_slug=self.sport_slug,
                variant=self.sport_variant,
                format=self.sport_format,
                metrics=self.sport_metrics,
            )
        except SportFieldError as exc:
            raise ValueError(str(exc)) from exc
        if self.sport_slug is not None:
            self.sport_category = SportCategory(str(resolved["sport_category"]))
            if self.category is None:
                self.category = activity_category_for_sport(str(resolved["sport_category"]))
        if self.category is None:
            raise ValueError("category is required when no sport_slug is provided")
        return self


class ActivityCreate(ActivityBase):
    """Payload to create an activity. Host defaults to the caller."""

    @model_validator(mode="after")
    def _check_window(self) -> "ActivityCreate":
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class ActivityUpdate(BaseModel):
    """Partial update; every field optional. Host/owner-only at the router."""

    title: str | None = Field(default=None, min_length=3, max_length=160)
    sport_slug: str | None = Field(default=None, max_length=40)
    sport_variant: str | None = Field(default=None, max_length=40)
    sport_format: str | None = Field(default=None, max_length=40)
    sport_metrics: list[str] | None = None
    activity_type: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=8000)
    category: ActivityCategory | None = None
    skill_level: SkillLevel | None = None
    visibility: ActivityVisibility | None = None
    venue_id: uuid.UUID | None = None
    venue_court_id: uuid.UUID | None = None
    club_id: uuid.UUID | None = None
    category_link_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_participants: int | None = Field(default=None, ge=1, le=1000)
    cost_per_person_cents: int | None = Field(default=None, ge=0, le=10_000_000)
    is_cancelled: bool | None = None


class ActivityParticipantRead(ORMModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    user_id: uuid.UUID
    status: ParticipantStatus
    is_host: bool
    joined_at: datetime | None = None


class ActivityRead(ORMModel):
    id: uuid.UUID
    host_id: uuid.UUID
    venue_id: uuid.UUID | None = None
    venue_court_id: uuid.UUID | None = None
    club_id: uuid.UUID | None = None
    category_link_id: uuid.UUID | None = None
    title: str
    sport_slug: str | None = None
    sport_category: SportCategory | None = None
    sport_variant: str | None = None
    sport_format: str | None = None
    sport_metrics: list[str] | None = None
    activity_type: str | None = None
    venue: VenueBrief | None = None
    description: str | None = None
    category: ActivityCategory
    skill_level: SkillLevel
    visibility: ActivityVisibility
    starts_at: datetime
    ends_at: datetime | None = None
    max_participants: int
    cost_per_person_cents: int
    currency: str
    is_cancelled: bool
    created_at: datetime
    participant_count: int = 0
    waitlist_count: int = 0


class MyActivityRead(ActivityRead):
    """An activity in the caller's "Aktivitas Saya" view.

    Extends :class:`ActivityRead` with the caller-specific view: which real
    state bucket it falls in (upcoming/waitlisted/past/hosting), the caller's
    own participation status and attendance outcome, plus the human sport and
    venue/court labels so a client can render the row without extra lookups.
    """

    #: Bucket for the caller: ``upcoming`` | ``waitlisted`` | ``past`` | ``hosting``.
    state: str = "upcoming"
    #: The caller's participation status for this activity (None if host-only).
    participation_status: ParticipantStatus | None = None
    #: True when the caller created (hosts) the activity.
    is_host: bool = False
    #: Sport catalog label (Indonesian) for ``sport_slug``.
    sport_label: str | None = None
    #: Sport catalog label (English) for ``sport_slug``.
    sport_label_en: str | None = None
    #: Venue display name.
    venue_label: str | None = None
    #: Court/resource display name when the activity is on a specific court.
    court_label: str | None = None
    #: Attendance outcome for past items: attended | no_show | cancelled | <status>.
    attendance: str | None = None


class MyActivityGroups(BaseModel):
    """The caller's activities split by real state."""

    upcoming: list[MyActivityRead] = Field(default_factory=list)
    waitlisted: list[MyActivityRead] = Field(default_factory=list)
    past: list[MyActivityRead] = Field(default_factory=list)
    hosting: list[MyActivityRead] = Field(default_factory=list)


class MyActivitiesRead(BaseModel):
    """Envelope for ``GET /activities/mine``.

    Keeps the standard pagination envelope (``items``/``total``/``limit``/
    ``offset``) used across the codebase, and adds ``groups`` split by real
    state so callers get both a flat page and the four buckets.
    """

    items: list[MyActivityRead] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
    groups: MyActivityGroups = Field(default_factory=MyActivityGroups)
