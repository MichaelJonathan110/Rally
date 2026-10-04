"""Booking endpoints: list/create, detail, cancel (booker-only)."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.models.enums import BookingStatus
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.common import Page
from app.schemas.payment import (
    BalanceRead,
    PaymentCreate,
    PaymentRead,
    RefundRead,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[BookingRead])
def list_bookings(
    current_user: CurrentUser,
    db: DbSession,
    mine: bool = True,
    venue_court_id: Annotated[uuid.UUID | None, Query()] = None,
    activity_id: Annotated[uuid.UUID | None, Query()] = None,
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[BookingRead]:
    """List bookings. By default only the caller's own bookings are returned."""
    service = BookingService(db)
    rows, total = service.list_bookings(
        booked_by_id=current_user.id if mine else None,
        venue_court_id=venue_court_id,
        activity_id=activity_id,
        status=str(status_filter) if status_filter else None,
        limit=limit,
        offset=offset,
    )
    return Page[BookingRead](
        items=[BookingRead.model_validate(b) for b in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate, current_user: CurrentUser, db: DbSession
) -> BookingRead:
    booking = BookingService(db).create(current_user.id, payload.model_dump())
    return BookingRead.model_validate(booking)


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: uuid.UUID, db: DbSession) -> BookingRead:
    return BookingRead.model_validate(BookingService(db).get(booking_id))


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> BookingRead:
    booking = BookingService(db).cancel(booking_id, current_user.id)
    return BookingRead.model_validate(booking)


@router.post("/{booking_id}/confirm", response_model=BookingRead)
def confirm_booking(
    booking_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> BookingRead:
    """Confirm a booking (booker or activity host)."""
    booking = BookingService(db).confirm(booking_id, current_user.id)
    return BookingRead.model_validate(booking)


@router.post("/{booking_id}/complete", response_model=BookingRead)
def complete_booking(
    booking_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> BookingRead:
    """Complete a confirmed booking (booker or activity host). Terminal state."""
    booking = BookingService(db).complete(booking_id, current_user.id)
    return BookingRead.model_validate(booking)


@router.post("/{booking_id}/pay", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def pay_booking(
    booking_id: uuid.UUID,
    payload: PaymentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> PaymentRead:
    """Pay the caller's share of a booking. Idempotent via idempotency_key."""
    from app.services.payment_service import PaymentService

    payment = PaymentService(db).pay(
        booking_id,
        current_user.id,
        idempotency_key=payload.idempotency_key,
        amount_cents=payload.amount_cents,
    )
    return PaymentRead.model_validate(payment)


@router.get("/{booking_id}/balance", response_model=BalanceRead)
def booking_balance(booking_id: uuid.UUID, db: DbSession) -> BalanceRead:
    """Total / paid / outstanding for a booking."""
    return BalanceRead.model_validate(BookingService(db).balance(booking_id))


@router.post("/{booking_id}/refund", response_model=list[RefundRead])
def refund_booking(
    booking_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> list[RefundRead]:
    """Refund all captured payments (booker or activity host only)."""
    from app.services.payment_service import PaymentService

    service = BookingService(db)
    booking = service.get(booking_id)
    service._require_host_or_booker(booking, current_user.id)
    refunds = PaymentService(db).refund_booking(booking_id, reason="manual refund")
    return [RefundRead.model_validate(r) for r in refunds]
