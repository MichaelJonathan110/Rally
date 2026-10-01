"""Activity, ActivityCategoryLink and ActivityParticipant models.

The activity engine is config-driven: categories/types/configs live in the
database and behaviour is resolved from those rows, never hardcoded per-activity
branches in components.
"""
from __future__ import annotations

import uuid
from datetime import datetime

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
from app.models.enums import (
    ActivityCategory,
    ActivityVisibility,
    ParticipantStatus,
    SkillLevel,
    pg_enum,
)


class ActivityCategoryLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A config-driven category row (e.g. sports, games, outdoor)."""

    __tablename__ = "activity_categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_activity_categories_slug"),
    )

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
    category_link_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activity_categories.id", ondelete="SET NULL"),
        index=True,
    )

    title: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
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

    participants: Mapped[list[ActivityParticipant]] = relationship(
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
