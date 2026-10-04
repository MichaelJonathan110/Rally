"""Venue, VenueCourt and VenueAvailability models."""
from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ActivityCategory, pg_enum


class Venue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "venues"

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    #: Province the city belongs to (e.g. "Jawa Barat"), for the city/province picker.
    province: Mapped[str | None] = mapped_column(String(80), index=True)
    #: Neighbourhood / kecamatan / kawasan (e.g. "Kemang", "Cihampelas", "Gubeng").
    area: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(2))
    #: Primary activity category the venue serves (sports, fitness, outdoor...).
    category: Mapped[ActivityCategory | None] = mapped_column(
        pg_enum(ActivityCategory, "activitycategory"), index=True
    )
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    #: The resource kind this venue provides (a venue_kind value from
    #: app.core.sports, e.g. "court", "field", "gym"). Lets the booking engine
    #: resolve which sport(s) can be played here.
    venue_kind: Mapped[str | None] = mapped_column(String(40), index=True)
    #: Sport slugs (app.core.sports) this venue supports.
    sport_slugs: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default=text("'[]'"), nullable=False
    )

    courts: Mapped[list[VenueCourt]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )


class VenueCourt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "venue_courts"
    __table_args__ = (UniqueConstraint("venue_id", "name", name="uq_venue_courts_venue_name"),)

    venue_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    surface: Mapped[str | None] = mapped_column(String(60))
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    hourly_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    #: Resource kind (venue_kind of the sport played on this resource).
    venue_kind: Mapped[str | None] = mapped_column(String(40), index=True)
    #: Human label of the resource (sports-catalog resource_label, e.g. "Court").
    resource_label: Mapped[str | None] = mapped_column(String(60))

    venue: Mapped[Venue] = relationship(back_populates="courts")
    availability: Mapped[list[VenueAvailability]] = relationship(
        back_populates="court", cascade="all, delete-orphan"
    )


class VenueAvailability(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A recurring weekly opening window for a court (0=Monday .. 6=Sunday)."""

    __tablename__ = "venue_availability"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_venue_availability_weekday"),
        CheckConstraint("opens_at < closes_at", name="ck_venue_availability_window"),
    )

    court_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("venue_courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    opens_at: Mapped[time] = mapped_column(Time, nullable=False)
    closes_at: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    court: Mapped[VenueCourt] = relationship(back_populates="availability")
