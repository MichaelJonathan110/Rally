"""Booking, Payment and PaymentSplit models.

Payment is a provider abstraction; the actual charge happens through a
configured provider (dev/mock provider is explicitly labelled). Amounts are
stored in integer minor units (cents) to avoid float rounding.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BookingStatus, PaymentStatus, SplitStatus, pg_enum


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    venue_court_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("venue_courts.id", ondelete="SET NULL"),
        index=True,
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activities.id", ondelete="SET NULL"), index=True
    )
    booked_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[BookingStatus] = mapped_column(
        pg_enum(BookingStatus, "bookingstatus"),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    # Idempotency: client-supplied key guarantees one booking per intent.
    idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payments: Mapped[list[Payment]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )
    splits: Mapped[list[PaymentSplit]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), index=True
    )
    payer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, "paymentstatus"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(120), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    booking: Mapped[Booking | None] = relationship(back_populates="payments")


class PaymentSplit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_splits"
    __table_args__ = (
        UniqueConstraint("payment_id", "user_id", name="uq_payment_splits_payment_user"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    share_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[SplitStatus] = mapped_column(
        pg_enum(SplitStatus, "splitstatus"),
        default=SplitStatus.PENDING,
        nullable=False,
        index=True,
    )

    booking: Mapped[Booking | None] = relationship(back_populates="splits")
