"""Payment provider abstraction package.

Exposes the provider interface, the deterministic in-process mock provider and
the env-driven factory. Real rails (Stripe) plug in behind the same interface.
"""
from __future__ import annotations

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
from app.services.payments.factory import (
    SUPPORTED_PROVIDERS,
    get_default_provider,
    get_payment_provider,
)
from app.services.payments.mock_provider import SIGNATURE_HEADER, MockProvider

__all__ = [
    "PaymentProvider",
    "PaymentIntent",
    "PaymentIntentStatus",
    "RefundResult",
    "RefundOutcome",
    "WebhookEvent",
    "WebhookVerificationError",
    "PaymentProviderError",
    "MockProvider",
    "SIGNATURE_HEADER",
    "get_payment_provider",
    "get_default_provider",
    "SUPPORTED_PROVIDERS",
]
