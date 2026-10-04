"""Booking, Payment, PaymentSplit and Refund models.

Payment is a provider abstraction; the actual charge happens through a
configured provider (dev/mock provider is explicitly labelled). Amounts are
stored in integer minor units (cents) to avoid float rounding.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    BookingStatus,
    PaymentStatus,
    RefundStatus,
    SplitStatus,
    pg_enum,
)
from app.models.venue import VenueCourt


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_bookings_window"),
    )

    venue_court_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("venue_courts.id", ondelete="SET NULL"),
        index=True,
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activities.id", ondelete="SET NULL"), index=True
    )
    #: Sport (app.core.sports slug) this booking is for.
    sport_slug: Mapped[str | None] = mapped_column(String(40), index=True)
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
    #: The bookable resource (VenueCourt) this booking holds; price + sport
    #: validation are derived from it, never from a free-form client number.
    venue_court: Mapped[VenueCourt | None] = relationship("VenueCourt", lazy="joined")

    # -- derived read-only fields exposed on the API payload -----------------
    @property
    def resource_kind(self) -> str | None:
        return self.venue_court.venue_kind if self.venue_court is not None else None

    @property
    def resource_label(self) -> str | None:
        return self.venue_court.resource_label if self.venue_court is not None else None

    @property
    def venue_name(self) -> str | None:
        court = self.venue_court
        if court is None or court.venue is None:
            return None
        return court.venue.name

    @property
    def payment_status(self) -> PaymentStatus:
        """Aggregate payment state across the booking's payment rows."""
        statuses = [p.status for p in self.payments]
        if not statuses:
            return PaymentStatus.PENDING
        if any(s == PaymentStatus.REFUNDED for s in statuses):
            return PaymentStatus.REFUNDED
        if any(s == PaymentStatus.PENDING for s in statuses):
            return PaymentStatus.PENDING
        if any(s == PaymentStatus.PAID for s in statuses):
            return PaymentStatus.PAID
        if any(s == PaymentStatus.FAILED for s in statuses):
            return PaymentStatus.FAILED
        return PaymentStatus.PENDING


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_payments_amount"),
    )

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
    refunds: Mapped[list[Refund]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentSplit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_splits"
    __table_args__ = (
        UniqueConstraint("payment_id", "user_id", name="uq_payment_splits_payment_user"),
        CheckConstraint("share_cents >= 0", name="ck_payment_splits_share"),
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


class Refund(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_refunds_amount"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[RefundStatus] = mapped_column(
        pg_enum(RefundStatus, "refundstatus"),
        default=RefundStatus.PENDING,
        nullable=False,
        index=True,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(120), index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="refunds")
