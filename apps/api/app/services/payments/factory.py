"""Provider factory: pick the payment provider from the environment.

Selection order: explicit argument, then ``PAYMENT_PROVIDER`` env var, then the
default (``mock``). The mock provider is a real working implementation, so the
app is fully functional and testable with no external keys. Selecting ``stripe``
returns a documented skeleton that fails fast if keys are missing.
"""
from __future__ import annotations

import os
from functools import lru_cache

from app.services.payments.base import PaymentProvider
from app.services.payments.mock_provider import MockProvider
from app.services.payments.stripe_provider import StripeProvider

SUPPORTED_PROVIDERS = ("mock", "stripe")
DEFAULT_PROVIDER = "mock"


def get_payment_provider(name: str | None = None) -> PaymentProvider:
    """Return the configured :class:`PaymentProvider`.

    Unknown names raise ``ValueError`` rather than silently falling back, so a
    typo is caught immediately instead of charging via the wrong rail.
    """
    selected = (name or os.getenv("PAYMENT_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if selected == "mock":
        return MockProvider()
    if selected == "stripe":
        return StripeProvider()  # raises NotImplementedError if unconfigured
    raise ValueError(
        f"Unknown PAYMENT_PROVIDER {selected!r}; expected one of {SUPPORTED_PROVIDERS}"
    )


@lru_cache(maxsize=1)
def get_default_provider() -> PaymentProvider:
    """Cached process-wide default provider (used by the webhook endpoint)."""
    return get_payment_provider()
