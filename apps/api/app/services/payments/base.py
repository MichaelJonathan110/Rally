"""Payment provider abstraction (interface + value objects).

A *provider* is a swappable adapter that talks to a real payment rail (Stripe)
or to the in-process mock provider. The rest of the application depends only on
this interface, so RALLY is fully usable and testable without real API keys.

All monetary amounts are integer minor units (cents) to avoid float rounding.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class PaymentIntentStatus(StrEnum):
    """Lifecycle of a provider-side payment intent."""

    PENDING = "pending"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RefundOutcome(StrEnum):
    """Result of a provider-side refund request."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class PaymentProviderError(Exception):
    """Raised when the provider rejects an operation (invalid input, etc.)."""


class WebhookVerificationError(Exception):
    """Raised when an inbound webhook signature cannot be verified."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class PaymentIntent:
    """A provider-agnostic representation of a payment intent."""

    provider: str
    reference: str
    amount_cents: int
    currency: str
    status: PaymentIntentStatus
    idempotency_key: str
    client_secret: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RefundResult:
    """A provider-agnostic representation of a refund."""

    provider: str
    reference: str
    payment_reference: str
    amount_cents: int
    currency: str
    status: RefundOutcome
    created_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WebhookEvent:
    """A verified inbound webhook event, normalised across providers."""

    provider: str
    event_id: str
    event_type: str
    payment_reference: str | None
    payment_status: str | None
    raw: dict[str, Any] = field(default_factory=dict)


class PaymentProvider(ABC):
    """Abstract payment provider.

    Implementations must be deterministic and side-effect free with respect to
    the application database; they only talk to their own rail.
    """

    name: str = "abstract"

    @abstractmethod
    def create_payment_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentIntent:
        """Create (or return, for a repeated idempotency key) a payment intent."""

    @abstractmethod
    def confirm_payment(
        self, *, reference: str, idempotency_key: str | None = None
    ) -> PaymentIntent:
        """Confirm/capture a previously created payment intent."""

    @abstractmethod
    def refund(
        self,
        *,
        payment_reference: str,
        amount_cents: int,
        currency: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> RefundResult:
        """Refund all or part of a confirmed payment."""

    @abstractmethod
    def verify_webhook(self, *, payload: bytes, signature: str | None) -> WebhookEvent:
        """Verify a webhook signature and return the normalised event."""
