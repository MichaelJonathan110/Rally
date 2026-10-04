"""Payment business logic: charge a booking, gate confirmation, refund, balances.

This service is the only place that talks to a PaymentProvider. It keeps the
application database and the provider rail in step:

* Every payment write is keyed by a client-supplied idempotency_key - a
  repeated key returns the existing Payment row untouched (no double charge).
* Paying a booking charges the payer split through the provider and records a
  PAID payment with the provider reference.
* A booking is CONFIRMED only when its payments have genuinely succeeded: the
  server-side gate confirm_booking_if_settled runs after every capture and
  refuses to confirm unless a captured (PAID, provider-referenced) payment
  exists and nothing is still outstanding. A booking whose payment is still
  pending or failed is never treated as confirmed or paid anywhere.
* A declined provider charge is recorded as a FAILED payment and the booking is
  left unconfirmed, surfacing a clear PaymentDeclinedError (HTTP 402).
* Cancelling/refunding a paid booking refunds through the provider and moves the
  payment to REFUNDED and the booking to REFUNDED, consistently, once per
  payment (replays are idempotent).

Amounts are integer minor units (cents).
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PaymentDeclinedError,
    ValidationError,
)
from app.models.booking import Booking, Payment, Refund
from app.models.enums import (
    BookingStatus,
    NotificationType,
    PaymentStatus,
    RefundStatus,
    SplitStatus,
)
from app.repositories.payment import PaymentRepository
from app.services.notification_service import NotificationService
from app.services.payments import (
    PaymentProvider,
    PaymentProviderError,
    get_default_provider,
)


class PaymentService:
    def __init__(self, db: Session, provider: PaymentProvider | None = None) -> None:
        self.db = db
        self.repo = PaymentRepository(db)
        self.provider = provider or get_default_provider()

    # -- reads ---------------------------------------------------------------
    def get(self, payment_id: uuid.UUID) -> Payment:
        payment = self.repo.get(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment

    def balance(self, booking_id: uuid.UUID) -> dict[str, int | str]:
        """Return the money picture for a booking: total / paid / outstanding."""
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        total = int(booking.total_price_cents)
        paid = self.repo.paid_cents(booking_id)
        return {
            "booking_id": str(booking_id),
            "currency": booking.currency,
            "total_cents": total,
            "paid_cents": paid,
            "outstanding_cents": max(total - paid, 0),
        }

    def outstanding_cents(self, booking_id: uuid.UUID) -> int:
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return max(int(booking.total_price_cents) - self.repo.paid_cents(booking_id), 0)

    # -- server-side confirmation gate ---------------------------------------
    def _has_captured_payment(self, booking_id: uuid.UUID) -> bool:
        """True iff at least one payment was really captured by the provider."""
        return bool(self.repo.charged_payments(booking_id))

    def confirm_booking_if_settled(self, booking_id: uuid.UUID) -> Booking | None:
        """Confirm a booking ONLY when its payment has genuinely succeeded.

        This is the single server-side gate on the payment -> confirmation
        transition. It confirms the booking (and returns it) when, and only
        when, a captured payment exists and nothing is still outstanding.
        Otherwise it leaves the booking untouched and returns None:

        * a booking with a pending/failed payment is never confirmed;
        * a terminal booking (cancelled/refunded/completed) is never revived.

        The caller owns the transaction/commit.
        """
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.status in (
            BookingStatus.CANCELLED,
            BookingStatus.REFUNDED,
            BookingStatus.COMPLETED,
        ):
            return None
        if self.repo.paid_cents(booking_id) <= 0:
            return None
        if self.outstanding_cents(booking_id) != 0:
            return None
        if not self._has_captured_payment(booking_id):
            return None
        if booking.status == BookingStatus.CONFIRMED:
            return None  # already confirmed - no-op
        booking.status = BookingStatus.CONFIRMED
        return booking

    # -- writes --------------------------------------------------------------
    def pay(
        self,
        booking_id: uuid.UUID,
        payer_id: uuid.UUID,
        *,
        idempotency_key: str,
        amount_cents: int | None = None,
        provider_name: str | None = None,
    ) -> Payment:
        """Charge payer_id for their share of booking_id.

        Idempotent: replaying idempotency_key returns the same payment row and
        never double-charges. On provider decline the payment is recorded as
        FAILED, the booking is left unconfirmed, and a PaymentDeclinedError is
        raised (HTTP 402).
        """
        if not idempotency_key:
            raise ValidationError("idempotency_key is required")

        existing = self.repo.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing  # idempotent replay - same row, no new charge

        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.REFUNDED):
            raise ConflictError("Cannot pay a cancelled or refunded booking")

        split = self.repo.get_split_for_user(booking_id, payer_id)
        if split is None:
            raise NotFoundError("No payment split for this user on this booking")
        if split.status == SplitStatus.PAID:
            raise ConflictError("This split has already been paid")

        charge_cents = split.share_cents if amount_cents is None else amount_cents
        if charge_cents <= 0:
            raise ValidationError("amount_cents must be positive")
        if charge_cents > split.share_cents:
            raise ValidationError("amount_cents exceeds the outstanding split share")

        # Talk to the provider rail (mock by default). Deterministic + idempotent.
        try:
            intent = self.provider.create_payment_intent(
                amount_cents=charge_cents,
                currency=booking.currency,
                idempotency_key=idempotency_key,
                metadata={"booking_id": str(booking_id), "payer_id": str(payer_id)},
            )
            confirmed = self.provider.confirm_payment(reference=intent.reference)
        except PaymentProviderError as exc:
            # Decline: persist a FAILED payment and never confirm the booking.
            self.record_failure(
                booking_id,
                payer_id,
                idempotency_key=idempotency_key,
                reason=str(exc),
            )
            raise PaymentDeclinedError(str(exc)) from exc

        payment = self.repo.get_pending_for_payer(booking_id, payer_id)
        if payment is None:
            payment = Payment(
                booking_id=booking.id,
                payer_id=payer_id,
                amount_cents=charge_cents,
                currency=booking.currency,
            )
            self.repo.add(payment)
        payment.amount_cents = charge_cents
        payment.status = PaymentStatus.PAID
        payment.provider = provider_name or confirmed.provider
        payment.provider_reference = confirmed.reference
        payment.idempotency_key = idempotency_key

        split.status = SplitStatus.PAID
        self.db.flush()  # persist the split before recomputing the balance

        # The single gate: only a fully captured balance confirms the booking.
        just_confirmed = self.confirm_booking_if_settled(booking_id) is not None
        self.repo.commit()
        self.repo.refresh(payment)

        # In-app notifications (PART D): payment received, and booking confirmed
        # when this settlement cleared the outstanding balance.
        notifications = NotificationService(self.db)
        notifications.notify(
            payer_id,
            type=NotificationType.PAYMENT,
            title="Payment received",
            body=f"Your payment of {payment.amount_cents} {payment.currency} was received.",
            data={
                "booking_id": str(booking_id),
                "payment_id": str(payment.id),
                "amount_cents": payment.amount_cents,
            },
        )
        if just_confirmed:
            notifications.notify(
                booking.booked_by_id,
                type=NotificationType.BOOKING,
                title="Booking confirmed",
                body="Your booking is fully paid and confirmed.",
                data={"booking_id": str(booking_id), "status": str(booking.status)},
            )
        return payment

    def record_failure(
        self,
        booking_id: uuid.UUID,
        payer_id: uuid.UUID,
        *,
        idempotency_key: str | None = None,
        reason: str | None = None,
    ) -> Payment:
        """Persist a FAILED payment for a declined charge.

        The booking is deliberately left untouched (unconfirmed): a failed
        payment must never gate the booking into a paid/confirmed state.
        Idempotent on idempotency_key.
        """
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")

        payment: Payment | None = None
        if idempotency_key:
            payment = self.repo.get_by_idempotency_key(idempotency_key)
        if payment is None:
            payment = self.repo.get_pending_for_payer(booking_id, payer_id)
        if payment is None:
            payment = Payment(
                booking_id=booking.id,
                payer_id=payer_id,
                amount_cents=booking.total_price_cents,
                currency=booking.currency,
            )
            self.repo.add(payment)
        payment.status = PaymentStatus.FAILED
        if idempotency_key:
            payment.idempotency_key = idempotency_key
        self.repo.commit()
        self.repo.refresh(payment)
        return payment

    def refund_booking(
        self,
        booking_id: uuid.UUID,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> list[Refund]:
        """Refund every captured payment on a booking (idempotent per payment).

        Returns the refund rows; already-refunded payments are skipped so a
        repeated cancel does not double-refund. When anything is refunded the
        booking and its payments/splits move to REFUNDED consistently.
        """
        booking = self.db.get(Booking, booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")

        self.db.flush()
        refunds: list[Refund] = []
        for payment in self.repo.charged_payments(booking_id):
            result = self.provider.refund(
                payment_reference=payment.provider_reference or "",
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                reason=reason,
                idempotency_key=idempotency_key or f"refund:{payment.id}",
            )
            refund = Refund(
                payment_id=payment.id,
                requested_by_id=booking.booked_by_id,
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                reason=reason,
                status=RefundStatus.PROCESSED,
                provider_reference=result.reference,
            )
            self.repo.add_refund(refund)
            payment.status = PaymentStatus.REFUNDED
            refunds.append(refund)

        for split in self.repo.list_splits(booking_id):
            if split.status == SplitStatus.PAID:
                split.status = SplitStatus.REFUNDED

        if refunds:
            booking.status = BookingStatus.REFUNDED
        self.repo.commit()
        return refunds

    def list_refunds(self, booking_id: uuid.UUID) -> list[Refund]:
        return list(self.repo.list_refunds_for_booking(booking_id))
