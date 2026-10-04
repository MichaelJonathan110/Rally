"""Payment, split, refund and balance schemas.

Amounts are integer minor units (cents). Payment writes are idempotent via a
client-supplied ``idempotency_key``.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PaymentStatus, RefundStatus, SplitStatus
from app.schemas.common import ORMModel


class PaymentSplitRead(ORMModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    booking_id: uuid.UUID | None = None
    user_id: uuid.UUID
    share_cents: int
    currency: str
    status: SplitStatus


class PaymentCreate(BaseModel):
    """Charge a participant for their share of a booking."""

    idempotency_key: str = Field(min_length=8, max_length=80)
    amount_cents: int | None = Field(default=None, ge=1, le=100_000_000)


class PaymentRead(ORMModel):
    id: uuid.UUID
    booking_id: uuid.UUID | None = None
    payer_id: uuid.UUID
    amount_cents: int
    currency: str
    status: PaymentStatus
    provider: str
    provider_reference: str | None = None
    idempotency_key: str | None = None
    created_at: datetime


class RefundRead(ORMModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    amount_cents: int
    currency: str
    reason: str | None = None
    status: RefundStatus
    provider_reference: str | None = None
    created_at: datetime


class BalanceRead(BaseModel):
    booking_id: uuid.UUID
    currency: str
    total_cents: int
    paid_cents: int
    outstanding_cents: int
