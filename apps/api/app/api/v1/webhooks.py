"""Payment provider webhook endpoint.

POST /webhooks/payments/{provider} - the provider signs the raw body; we verify
the signature through the provider adapter and then update the local payment
status idempotently (replaying the same event never double-applies).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.booking import Payment
from app.models.enums import PaymentStatus
from app.services.payments import (
    SUPPORTED_PROVIDERS,
    WebhookVerificationError,
    get_payment_provider,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

DbSession = Annotated[Session, Depends(get_db)]

#: Map a provider-side status string to our internal PaymentStatus.
_STATUS_MAP = {
    "succeeded": PaymentStatus.PAID,
    "paid": PaymentStatus.PAID,
    "authorized": PaymentStatus.AUTHORIZED,
    "processing": PaymentStatus.PENDING,
    "pending": PaymentStatus.PENDING,
    "failed": PaymentStatus.FAILED,
    "canceled": PaymentStatus.CANCELLED,
    "cancelled": PaymentStatus.CANCELLED,
    "refunded": PaymentStatus.REFUNDED,
}


@router.post("/payments/{provider}", status_code=status.HTTP_200_OK)
async def payment_webhook(
    provider: str,
    request: Request,
    db: DbSession,
    x_rally_signature: Annotated[str | None, Header(alias="X-Rally-Signature")] = None,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> dict[str, object]:
    """Verify a provider webhook and idempotently update the payment status."""
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider {provider!r}")

    adapter = get_payment_provider(provider)
    payload = await request.body()
    signature = x_rally_signature or stripe_signature

    try:
        event = adapter.verify_webhook(payload=payload, signature=signature)
    except WebhookVerificationError as exc:
        # Signature failure is a client error (400), never silently accepted.
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    reference = event.payment_reference
    if not reference:
        return {"ok": True, "applied": False, "detail": "no payment reference"}

    payment = db.scalar(select(Payment).where(Payment.provider_reference == reference))
    if payment is None:
        return {"ok": True, "applied": False, "detail": "unknown payment reference"}

    new_status = _STATUS_MAP.get((event.payment_status or "").lower())
    if new_status is None:
        return {"ok": True, "applied": False, "detail": "unmapped status"}

    # Idempotent: an already-applied status is a no-op.
    if payment.status == new_status:
        return {
            "ok": True,
            "applied": False,
            "idempotent": True,
            "payment_id": str(payment.id),
            "status": str(payment.status),
        }

    payment.status = new_status
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return {
        "ok": True,
        "applied": True,
        "event_id": event.event_id,
        "payment_id": str(payment.id),
        "status": str(payment.status),
    }
