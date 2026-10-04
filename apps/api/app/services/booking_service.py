"""Booking business logic: price derivation, payment splits, idempotency.

The payment provider is a swappable abstraction (mock by default) - see
app.services.payments. Totals are integer cents. A booking is split equally
among participants, or by explicit custom shares that must sum to the total.
Status flow: PENDING -> CONFIRMED -> COMPLETED (terminal), with CANCELLED and
REFUNDED as terminal alternatives. Only the booker or the activity host/owner may
transition a booking; cancelling a paid booking triggers refunds.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.activity import Activity
from app.models.booking import Booking, Payment, PaymentSplit
from app.models.enums import BookingStatus, NotificationType, PaymentStatus, SplitStatus
from app.repositories.booking import BookingRepository
from app.repositories.venue import VenueRepository
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService


class BookingService:
    def __init__(self, db: Session, provider: object | None = None) -> None:
        self.db = db
        self.repo = BookingRepository(db)
        self.venues = VenueRepository(db)
        self.payments = PaymentService(db, provider=provider)
        self.notifications = NotificationService(db)

    def get(self, booking_id: uuid.UUID) -> Booking:
        booking = self.repo.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return booking

    def list_bookings(
        self,
        *,
        booked_by_id: uuid.UUID | None = None,
        venue_court_id: uuid.UUID | None = None,
        activity_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Booking], int]:
        rows, total = self.repo.list(
            booked_by_id=booked_by_id,
            venue_court_id=venue_court_id,
            activity_id=activity_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return list(rows), total

    # -- create --------------------------------------------------------------
    def create(self, booked_by_id: uuid.UUID, data: dict) -> Booking:
        idempotency_key = data.get("idempotency_key")
        if idempotency_key:
            existing = self.repo.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing  # idempotent replay

        court_id = data.get("venue_court_id")
        starts_at = data["starts_at"]
        ends_at = data["ends_at"]
        total_price_cents = data.pop("total_price_cents", None)
        split_ids = list(data.pop("split_between_user_ids", []) or [])
        custom_splits = list(data.pop("custom_splits", []) or [])

        court = None
        if court_id is not None:
            court = self.venues.get_court(court_id)
            if court is None:
                raise ValidationError("Unknown venue_court_id")
            conflicts = self.repo.overlapping(court_id, starts_at, ends_at)
            if conflicts:
                raise ConflictError("Court is already booked for that window")

        if total_price_cents is None:
            total_price_cents = self._derive_price(court, starts_at, ends_at)

        booking = Booking(
            booked_by_id=booked_by_id,
            total_price_cents=total_price_cents,
            **data,
        )
        self.repo.add(booking)

        # Provider-abstracted payment intent for the full amount (PENDING until paid).
        payment = Payment(
            booking_id=booking.id,
            payer_id=booked_by_id,
            amount_cents=total_price_cents,
            currency=booking.currency,
            status=PaymentStatus.PENDING,
            provider=self.payments.provider.name,
        )
        self.db.add(payment)
        self.db.flush()

        shares = self._resolve_shares(
            total_price_cents, booked_by_id, split_ids, custom_splits
        )
        for user_id, share in shares:
            self.db.add(
                PaymentSplit(
                    payment_id=payment.id,
                    booking_id=booking.id,
                    user_id=user_id,
                    share_cents=share,
                    currency=booking.currency,
                    status=SplitStatus.PENDING,
                )
            )
        self.repo.commit()
        self.repo.refresh(booking)
        return booking

    # -- status transitions --------------------------------------------------
    def confirm(self, booking_id: uuid.UUID, actor_id: uuid.UUID) -> Booking:
        """Manually confirm a booking (booker or activity host)."""
        booking = self.get(booking_id)
        self._require_host_or_booker(booking, actor_id)
        if booking.status == BookingStatus.COMPLETED:
            raise ConflictError("Cannot confirm a completed booking")
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.REFUNDED):
            raise ConflictError("Cannot confirm a cancelled or refunded booking")
        booking.status = BookingStatus.CONFIRMED
        self.repo.commit()
        self.repo.refresh(booking)
        self._notify(booking, NotificationType.BOOKING, "Booking confirmed")
        return booking

    def cancel(self, booking_id: uuid.UUID, actor_id: uuid.UUID) -> Booking:
        """Cancel a booking; only the booker or the activity host may do so.

        A booking with captured payments is refunded (-> REFUNDED); otherwise it
        is simply CANCELLED.
        """
        booking = self.get(booking_id)
        self._require_host_or_booker(booking, actor_id)
        if booking.status == BookingStatus.COMPLETED:
            raise ConflictError("Cannot cancel a completed booking")
        if booking.status in (BookingStatus.CANCELLED, BookingStatus.REFUNDED):
            raise ConflictError("Booking is already cancelled")

        refunds = self.payments.refund_booking(
            booking_id, reason="booking cancelled", idempotency_key=f"cancel:{booking_id}"
        )
        if refunds:
            booking.status = BookingStatus.REFUNDED
        else:
            booking.status = BookingStatus.CANCELLED
        self.repo.commit()
        self.repo.refresh(booking)
        self._notify(
            booking,
            NotificationType.BOOKING,
            "Booking cancelled",
            body="The booking was cancelled." + (" Refund issued." if refunds else ""),
        )
        return booking

    def complete(self, booking_id: uuid.UUID, actor_id: uuid.UUID) -> Booking:
        """Complete a CONFIRMED booking (booker or activity host). Terminal state.

        Server-enforced state machine: only a CONFIRMED booking may be completed.
        Pending, cancelled, refunded and already-completed bookings are rejected
        as illegal transitions (409). Only the booker or the activity host may
        complete a booking (403 otherwise).
        """
        booking = self.get(booking_id)
        self._require_host_or_booker(booking, actor_id)
        if booking.status == BookingStatus.COMPLETED:
            raise ConflictError("Booking is already completed")
        if booking.status != BookingStatus.CONFIRMED:
            raise ConflictError(
                f"Illegal transition: cannot complete a {booking.status} booking; "
                "only confirmed bookings can be completed"
            )
        booking.status = BookingStatus.COMPLETED
        self.repo.commit()
        self.repo.refresh(booking)
        self._notify(booking, NotificationType.BOOKING, "Booking completed")
        return booking

    def balance(self, booking_id: uuid.UUID) -> dict:
        return self.payments.balance(booking_id)

    # -- helpers -------------------------------------------------------------
    def _require_host_or_booker(self, booking: Booking, actor_id: uuid.UUID) -> None:
        if actor_id == booking.booked_by_id:
            return
        host_id = None
        if booking.activity_id is not None:
            activity = self.db.get(Activity, booking.activity_id)
            host_id = activity.host_id if activity is not None else None
        if host_id is not None and actor_id == host_id:
            return
        raise PermissionDeniedError(
            "Only the booker or the activity host may perform this action"
        )

    def _notify(
        self,
        booking: Booking,
        type: NotificationType,
        title: str,
        body: str | None = None,
    ) -> None:
        self.notifications.notify(
            booking.booked_by_id,
            type=type,
            title=title,
            body=body,
            data={"booking_id": str(booking.id), "status": str(booking.status)},
        )

    @staticmethod
    def _resolve_shares(
        total: int,
        booked_by_id: uuid.UUID,
        split_ids: list[uuid.UUID],
        custom_splits: list[dict],
    ) -> list[tuple[uuid.UUID, int]]:
        """Return (user_id, share_cents) rows that always sum to the total."""
        if custom_splits:
            seen: set[uuid.UUID] = set()
            resolved: list[tuple[uuid.UUID, int]] = []
            for row in custom_splits:
                user_id = uuid.UUID(str(row["user_id"]))
                share = int(row["share_cents"])
                if share < 0:
                    raise ValidationError("share_cents must be >= 0")
                if user_id in seen:
                    raise ValidationError("custom_splits must be unique per user")
                seen.add(user_id)
                resolved.append((user_id, share))
            if sum(share for _, share in resolved) != total:
                raise ValidationError("custom_splits must sum to total_price_cents")
            return resolved

        payers = list(dict.fromkeys([booked_by_id, *split_ids]))
        return list(zip(payers, BookingService._split(total, len(payers)), strict=True))

    @staticmethod
    def _derive_price(court: object | None, starts_at: object, ends_at: object) -> int:
        if court is None:
            return 0
        hourly = getattr(court, "hourly_price_cents", 0)
        seconds = (ends_at - starts_at).total_seconds()  # type: ignore[operator]
        if seconds <= 0:
            raise ValidationError("ends_at must be after starts_at")
        hours = seconds / 3600
        return int(round(hourly * hours))

    @staticmethod
    def _split(total: int, parts: int) -> list[int]:
        if parts <= 0:
            return []
        base, remainder = divmod(total, parts)
        return [base + (1 if i < remainder else 0) for i in range(parts)]
