"""Booking, payment and split schemas.

Amounts are integer minor units (cents). Bookings are idempotent via a
client-supplied ``idempotency_key`` (natural unique constraint on the model).
The dev payment provider is explicitly labelled ``mock``.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BookingStatus, PaymentStatus, SplitStatus
from app.schemas.common import ORMModel


class PaymentSplitRead(ORMModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    user_id: uuid.UUID
    share_cents: int
    currency: str
    status: SplitStatus


class SplitInput(BaseModel):
    """An explicit per-user share of the booking total (must sum to total)."""

    user_id: uuid.UUID
    share_cents: int = Field(ge=0, le=100_000_000)


class PaymentRead(ORMModel):
    id: uuid.UUID
    booking_id: uuid.UUID | None = None
    payer_id: uuid.UUID
    amount_cents: int
    currency: str
    status: PaymentStatus
    provider: str
    provider_reference: str | None = None
    splits: list[PaymentSplitRead] = Field(default_factory=list)


class BookingBase(BaseModel):
    venue_court_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None
    #: Sport (app.core.sports slug) the booking is for.
    sport_slug: str | None = Field(default=None, max_length=40)
    starts_at: datetime
    ends_at: datetime
    currency: str = Field(default="USD", min_length=3, max_length=3)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=80)


class BookingCreate(BookingBase):
    """Create a booking.

    ``total_price_cents`` is optional; when omitted the service derives it from
    the court's hourly price and the booking window. ``split_between_user_ids``
    divides the total into equal payment splits (labelled dev/mock payment).
    """

    total_price_cents: int | None = Field(default=None, ge=0, le=100_000_000)
    split_between_user_ids: list[uuid.UUID] = Field(default_factory=list)
    custom_splits: list[SplitInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> "BookingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if self.venue_court_id is None and self.activity_id is None:
            raise ValueError("a booking needs a venue_court_id or an activity_id")
        if len(set(self.split_between_user_ids)) != len(self.split_between_user_ids):
            raise ValueError("split_between_user_ids must be unique")
        if self.split_between_user_ids and self.custom_splits:
            raise ValueError("use either split_between_user_ids or custom_splits")
        if self.custom_splits:
            user_ids = [s.user_id for s in self.custom_splits]
            if len(set(user_ids)) != len(user_ids):
                raise ValueError("custom_splits must be unique per user")
        return self


class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class BookingRead(ORMModel):
    id: uuid.UUID
    venue_court_id: uuid.UUID | None = None
    activity_id: uuid.UUID | None = None
    booked_by_id: uuid.UUID
    status: BookingStatus
    starts_at: datetime
    ends_at: datetime
    total_price_cents: int
    currency: str
    idempotency_key: str | None = None
    created_at: datetime
    #: Sport this booking is for (app.core.sports slug).
    sport_slug: str | None = None
    #: The venue name the booked resource belongs to.
    venue_name: str | None = None
    #: Booked resource kind + label (venue_kind / resource_label).
    resource_kind: str | None = None
    resource_label: str | None = None
    #: Aggregate payment status derived from the booking's payment rows.
    payment_status: PaymentStatus | None = None
    payments: list[PaymentRead] = Field(default_factory=list)
    splits: list[PaymentSplitRead] = Field(default_factory=list)
