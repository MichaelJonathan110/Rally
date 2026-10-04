"""Stripe payment provider (skeleton).

RALLY ships a real, working ``mock`` provider so the app is usable without any
API keys. This Stripe adapter is a *documented skeleton*: it validates that the
required configuration is present and raises a clear, actionable
``NotImplementedError`` when it is not (and until the live rail is wired).

It is intentionally NOT faked - no silent success, no placeholder charges.
"""
from __future__ import annotations

import os
from typing import Any

from app.services.payments.base import (
    PaymentIntent,
    PaymentProvider,
    RefundResult,
    WebhookEvent,
)

_MISSING_KEY_MSG = (
    "Stripe provider is not configured. Set STRIPE_SECRET_KEY (and "
    "STRIPE_WEBHOOK_SECRET) to enable it, or set PAYMENT_PROVIDER=mock to use "
    "the built-in deterministic provider. The Stripe rail is a documented "
    "skeleton and is not implemented yet."
)


def _require_keys() -> tuple[str, str | None]:
    secret = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise NotImplementedError(_MISSING_KEY_MSG)
    return secret, webhook_secret


class StripeProvider(PaymentProvider):
    """Skeleton Stripe adapter. See module docstring."""

    name = "stripe"

    def __init__(self) -> None:
        # Validate configuration eagerly so misconfiguration fails fast.
        _require_keys()

    def create_payment_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentIntent:
        raise NotImplementedError(_MISSING_KEY_MSG)

    def confirm_payment(
        self, *, reference: str, idempotency_key: str | None = None
    ) -> PaymentIntent:
        raise NotImplementedError(_MISSING_KEY_MSG)

    def refund(
        self,
        *,
        payment_reference: str,
        amount_cents: int,
        currency: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> RefundResult:
        raise NotImplementedError(_MISSING_KEY_MSG)

    def verify_webhook(self, *, payload: bytes, signature: str | None) -> WebhookEvent:
        raise NotImplementedError(_MISSING_KEY_MSG)
