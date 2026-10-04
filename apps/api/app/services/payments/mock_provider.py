"""Deterministic in-process payment provider.

This is a *real*, fully working provider - not fake data. It performs no
network calls and needs no API keys, so the whole application is usable and
testable out of the box. It behaves like a card rail:

* ``create_payment_intent`` returns a stable reference derived from the
  idempotency key; replaying the same key returns the *same* intent.
* ``confirm_payment`` moves an intent to ``succeeded`` (idempotent).
* ``refund`` moves funds back (idempotent per payment+amount).
* ``verify_webhook`` performs a genuine HMAC-SHA256 signature check.

References are deterministic (``pi_mock_<hash>`` / ``re_mock_<hash>``) so that
tests and idempotency assertions are reproducible across runs.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
from dataclasses import replace
from typing import Any

from app.services.payments.base import (
    PaymentIntent,
    PaymentIntentStatus,
    PaymentProvider,
    PaymentProviderError,
    RefundOutcome,
    RefundResult,
    WebhookEvent,
    WebhookVerificationError,
)

#: Header name a caller sends the webhook signature in.
SIGNATURE_HEADER = "X-Rally-Signature"

_DEFAULT_WEBHOOK_SECRET = "mock-webhook-secret"


def _digest(prefix: str, *parts: str) -> str:
    raw = "|".join(parts).encode("utf-8")
    return f"{prefix}{hashlib.sha256(raw).hexdigest()[:24]}"


class MockProvider(PaymentProvider):
    """In-memory, deterministic payment provider (the default)."""

    name = "mock"

    def __init__(self, webhook_secret: str | None = None) -> None:
        self._lock = threading.Lock()
        self._webhook_secret = (
            webhook_secret or os.getenv("MOCK_WEBHOOK_SECRET") or _DEFAULT_WEBHOOK_SECRET
        )
        self._intents: dict[str, PaymentIntent] = {}  # keyed by reference
        self._by_idempotency: dict[str, str] = {}  # idempotency_key -> reference
        self._refunds: dict[str, RefundResult] = {}  # keyed by refund reference

    # -- helpers -------------------------------------------------------------
    def reset(self) -> None:
        """Clear all in-memory state (used by tests)."""
        with self._lock:
            self._intents.clear()
            self._by_idempotency.clear()
            self._refunds.clear()

    def _require_intent(self, reference: str) -> PaymentIntent:
        intent = self._intents.get(reference)
        if intent is None:
            raise PaymentProviderError(f"Unknown payment reference: {reference}")
        return intent

    # -- PaymentProvider -----------------------------------------------------
    def create_payment_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentIntent:
        if amount_cents < 0:
            raise PaymentProviderError("amount_cents must be >= 0")
        if not idempotency_key:
            raise PaymentProviderError("idempotency_key is required")

        with self._lock:
            existing_ref = self._by_idempotency.get(idempotency_key)
            if existing_ref is not None:
                return self._intents[existing_ref]  # idempotent replay

            reference = _digest("pi_mock_", idempotency_key, str(amount_cents), currency)
            intent = PaymentIntent(
                provider=self.name,
                reference=reference,
                amount_cents=amount_cents,
                currency=currency.upper(),
                status=PaymentIntentStatus.REQUIRES_CONFIRMATION,
                idempotency_key=idempotency_key,
                client_secret=f"{reference}_secret",
                metadata=dict(metadata or {}),
            )
            self._intents[reference] = intent
            self._by_idempotency[idempotency_key] = reference
            return intent

    def confirm_payment(
        self, *, reference: str, idempotency_key: str | None = None
    ) -> PaymentIntent:
        with self._lock:
            intent = self._require_intent(reference)
            if intent.status == PaymentIntentStatus.SUCCEEDED:
                return intent  # already confirmed - idempotent
            if intent.status == PaymentIntentStatus.CANCELLED:
                raise PaymentProviderError("Cannot confirm a cancelled intent")
            confirmed = replace(intent, status=PaymentIntentStatus.SUCCEEDED)
            self._intents[reference] = confirmed
            return confirmed

    def refund(
        self,
        *,
        payment_reference: str,
        amount_cents: int,
        currency: str,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> RefundResult:
        if amount_cents <= 0:
            raise PaymentProviderError("refund amount_cents must be > 0")

        with self._lock:
            intent = self._require_intent(payment_reference)
            if intent.status != PaymentIntentStatus.SUCCEEDED:
                raise PaymentProviderError("Cannot refund a payment that is not succeeded")
            if amount_cents > intent.amount_cents:
                raise PaymentProviderError("Refund exceeds original payment amount")

            key = idempotency_key or f"{payment_reference}:{amount_cents}"
            existing = self._refunds.get(key)
            if existing is not None:
                return existing  # idempotent replay

            result = RefundResult(
                provider=self.name,
                reference=_digest("re_mock_", key),
                payment_reference=payment_reference,
                amount_cents=amount_cents,
                currency=currency.upper(),
                status=RefundOutcome.PROCESSED,
                metadata={"reason": reason} if reason else {},
            )
            self._refunds[key] = result
            return result

    def verify_webhook(self, *, payload: bytes, signature: str | None) -> WebhookEvent:
        if not signature:
            raise WebhookVerificationError("Missing webhook signature")
        expected = hmac.new(
            self._webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        # Constant-time compare; accept both bare and sha256=-prefixed forms.
        candidate = signature.split("=", 1)[-1]
        if not hmac.compare_digest(expected, candidate):
            raise WebhookVerificationError("Invalid webhook signature")

        try:
            data = json.loads(payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise WebhookVerificationError("Webhook payload is not valid JSON") from exc

        return WebhookEvent(
            provider=self.name,
            event_id=str(data.get("id") or _digest("evt_mock_", payload.hex())),
            event_type=str(data.get("type", "payment.updated")),
            payment_reference=data.get("payment_reference") or data.get("reference"),
            payment_status=data.get("status"),
            raw=data,
        )

    # -- test helper ---------------------------------------------------------
    def sign_payload(self, payload: bytes) -> str:
        """Produce the signature header value for ``payload`` (used by tests)."""
        return hmac.new(
            self._webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
