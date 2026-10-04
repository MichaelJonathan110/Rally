"""Activity engine models.

The activity engine is config-driven: categories/types/configs live in the
database and behaviour is resolved from those rows, never hardcoded per-activity
branches in components.

RALLY is sports-only: an activity names a sport from the sports catalog
(:mod:`app.core.sports`) via ``sport_slug`` and is categorised by that sport's
category (racket/team/combat/...) via ``sport_category``. The legacy generic
``category``/``activity_type`` columns are retained for backward compatibility
with rows created before the sports pivot.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.venue import Venue

from app.models.enums import (
    ActivityCategory,
    ActivityVisibility,
    ParticipantStatus,
    RecurrenceFrequency,
    SkillLevel,
    SportCategory,
    pg_enum,
)


class ActivityCategoryLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A config-driven category row (e.g. sports, games, outdoor)."""

    __tablename__ = "activity_categories"
    __table_args__ = (UniqueConstraint("slug", name="uq_activity_categories_slug"),)

    slug: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[ActivityCategory] = mapped_column(
        pg_enum(ActivityCategory, "activitycategory"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(60))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Activity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("max_participants > 0", name="ck_activities_max_participants"),
    )

    host_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL"), index=True
    )
    #: The specific bookable resource at the venue (Phase 2 sport-aware court).
    venue_court_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("venue_courts.id", ondelete="SET NULL"),
        index=True,
    )
    category_link_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity_categories.id", ondelete="SET NULL"),
        index=True,
    )
    club_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("clubs.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    #: SPORT slug from :mod:`app.core.sports` (e.g. padel, tennis, football).
    #: Nullable so rows created before the sports pivot stay valid.
    sport_slug: Mapped[str | None] = mapped_column(String(40), index=True)
    #: Sport category derived from ``sport_slug`` (racket/team/combat/...).
    sport_category: Mapped[SportCategory | None] = mapped_column(
        pg_enum(SportCategory, "sportcategory"), index=True
    )
    #: Sport-specific variant (must be one of the sport's catalog ``variants``).
    sport_variant: Mapped[str | None] = mapped_column(String(40))
    #: Sport-specific format (must be one of the sport's catalog ``formats``).
    sport_format: Mapped[str | None] = mapped_column(String(40))
    #: Sport-specific metrics tracked for this activity (subset of catalog).
    sport_metrics: Mapped[list[str] | None] = mapped_column(JSON)
    #: Legacy generic type inside ``category`` (kept for backward compatibility).
    activity_type: Mapped[str | None] = mapped_column(String(40), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[ActivityCategory] = mapped_column(
        pg_enum(ActivityCategory, "activitycategory"), nullable=False, index=True
    )
    skill_level: Mapped[SkillLevel] = mapped_column(
        pg_enum(SkillLevel, "skilllevel"), default=SkillLevel.ANY, nullable=False
    )
    visibility: Mapped[ActivityVisibility] = mapped_column(
        pg_enum(ActivityVisibility, "activityvisibility"),
        default=ActivityVisibility.PUBLIC,
        nullable=False,
        index=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_participants: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    cost_per_person_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    venue: Mapped[Venue | None] = relationship(lazy="joined")
    participants: Mapped[list[ActivityParticipant]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )
    recurrences: Mapped[list[ActivityRecurrence]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )


class ActivityParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activity_participants"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_activity_participants_activity_user"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        pg_enum(ParticipantStatus, "participantstatus"),
        default=ParticipantStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    is_host: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict[str, object] | None] = mapped_column(JSON)

    activity: Mapped[Activity] = relationship(back_populates="participants")


class ActivityRecurrence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recurrence rule for a recurring activity (RFC-5545-ish, simplified)."""

    __tablename__ = "activity_recurrences"
    __table_args__ = (
        CheckConstraint("interval_count >= 1", name="ck_activity_recurrences_interval"),
        CheckConstraint("occurrence_count >= 1", name="ck_activity_recurrences_occurrences"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        pg_enum(RecurrenceFrequency, "recurrencefrequency"), nullable=False, index=True
    )
    interval_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    by_weekday: Mapped[str | None] = mapped_column(String(20))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    activity: Mapped[Activity] = relationship(back_populates="recurrences")
