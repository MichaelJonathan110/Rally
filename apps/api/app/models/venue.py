"""Venue and VenueCourt models."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Venue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "venues"

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    address_line: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(2))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    courts: Mapped[list[VenueCourt]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )


class VenueCourt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "venue_courts"
    __table_args__ = (
        UniqueConstraint("venue_id", "name", name="uq_venue_courts_venue_name"),
    )

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

    venue: Mapped[Venue] = relationship(back_populates="courts")
