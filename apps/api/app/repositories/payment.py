"""Payment data access: payments, splits and refunds."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Payment, PaymentSplit, Refund
from app.models.enums import PaymentStatus, SplitStatus


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- payments ------------------------------------------------------------
    def get(self, payment_id: uuid.UUID) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def get_by_idempotency_key(self, key: str) -> Payment | None:
        return self.db.scalar(select(Payment).where(Payment.idempotency_key == key))

    def get_by_provider_reference(self, reference: str) -> Payment | None:
        return self.db.scalar(
            select(Payment).where(Payment.provider_reference == reference)
        )

    def get_pending_for_payer(
        self, booking_id: uuid.UUID, payer_id: uuid.UUID
    ) -> Payment | None:
        """The placeholder (unpaid) payment row for a booking + payer, if any."""
        return self.db.scalar(
            select(Payment)
            .where(
                Payment.booking_id == booking_id,
                Payment.payer_id == payer_id,
                Payment.status == PaymentStatus.PENDING,
            )
            .order_by(Payment.created_at.asc())
        )

    def list_for_booking(self, booking_id: uuid.UUID) -> Sequence[Payment]:
        return self.db.scalars(
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.asc())
        ).all()

    def add(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        return payment

    # -- splits --------------------------------------------------------------
    def list_splits(self, booking_id: uuid.UUID) -> Sequence[PaymentSplit]:
        return self.db.scalars(
            select(PaymentSplit)
            .where(PaymentSplit.booking_id == booking_id)
            .order_by(PaymentSplit.created_at.asc())
        ).all()

    def get_split_for_user(
        self, booking_id: uuid.UUID, user_id: uuid.UUID
    ) -> PaymentSplit | None:
        return self.db.scalar(
            select(PaymentSplit).where(
                PaymentSplit.booking_id == booking_id,
                PaymentSplit.user_id == user_id,
            )
        )

    def add_split(self, split: PaymentSplit) -> PaymentSplit:
        self.db.add(split)
        self.db.flush()
        return split

    def outstanding_cents(self, booking_id: uuid.UUID) -> int:
        """Total of splits that are still owed (not paid/waived/refunded)."""
        return int(
            self.db.scalar(
                select(func.coalesce(func.sum(PaymentSplit.share_cents), 0)).where(
                    PaymentSplit.booking_id == booking_id,
                    PaymentSplit.status == SplitStatus.PENDING,
                )
            )
            or 0
        )

    def paid_cents(self, booking_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.coalesce(func.sum(PaymentSplit.share_cents), 0)).where(
                    PaymentSplit.booking_id == booking_id,
                    PaymentSplit.status == SplitStatus.PAID,
                )
            )
            or 0
        )

    # -- refunds -------------------------------------------------------------
    def add_refund(self, refund: Refund) -> Refund:
        self.db.add(refund)
        self.db.flush()
        return refund

    def list_refunds_for_booking(self, booking_id: uuid.UUID) -> Sequence[Refund]:
        return self.db.scalars(
            select(Refund)
            .join(Payment, Refund.payment_id == Payment.id)
            .where(Payment.booking_id == booking_id)
            .order_by(Refund.created_at.asc())
        ).all()

    def charged_payments(self, booking_id: uuid.UUID) -> Sequence[Payment]:
        """Payments that actually captured funds (have a provider reference)."""
        return self.db.scalars(
            select(Payment).where(
                Payment.booking_id == booking_id,
                Payment.status == PaymentStatus.PAID,
                Payment.provider_reference.is_not(None),
            )
        ).all()

    # -- transaction ---------------------------------------------------------
    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: object) -> object:
        self.db.refresh(entity)
        return entity
