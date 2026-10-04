"""Notification business logic (in-app, DB-backed).

Notifications are persisted rows so they survive restarts and can be delivered
over any channel. Today the only channel is *in-app* (fetch via the API); the
``NotificationChannel`` seam is designed so a future push/email channel can be
added without changing call sites.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.enums import NotificationType
from app.models.social import Notification


class NotificationChannel(Protocol):
    """Delivery channel seam. The in-app channel just persists the row."""

    name: str

    def deliver(self, notification: Notification) -> None:  # pragma: no cover - trivial
        ...


class InAppChannel:
    """The default (and only) channel: the row itself is the delivery."""

    name = "in_app"

    def deliver(self, notification: Notification) -> None:
        # In-app notifications are read straight from the database; nothing to
        # push. Kept as a method so future channels share the same interface.
        return None


class NotificationService:
    def __init__(self, db: Session, channel: NotificationChannel | None = None) -> None:
        self.db = db
        self.channel = channel or InAppChannel()

    # -- writes --------------------------------------------------------------
    def notify(
        self,
        user_id: uuid.UUID,
        *,
        type: NotificationType,
        title: str,
        body: str | None = None,
        data: dict[str, Any] | None = None,
        commit: bool = True,
        event_key: str | None = None,
    ) -> Notification:
        """Create and persist a notification for ``user_id``.

        When ``event_key`` is supplied the call is idempotent: if a notification
        for the same user already carries that key in its payload, the existing
        row is returned instead of creating a duplicate.
        """
        payload: dict[str, Any] = dict(data or {})
        if event_key is not None:
            payload["event_key"] = event_key
            existing = self._find_by_event_key(user_id, event_key)
            if existing is not None:
                return existing
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=payload or None,
            is_read=False,
        )
        self.db.add(notification)
        self.db.flush()
        self.channel.deliver(notification)
        if commit:
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def notify_many(
        self,
        user_ids: list[uuid.UUID],
        *,
        type: NotificationType,
        title: str,
        body: str | None = None,
        data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> list[Notification]:
        """Fan out the same notification to several users (de-duplicated)."""
        created = [
            self.notify(
                uid, type=type, title=title, body=body, data=data, commit=False
            )
            for uid in dict.fromkeys(user_ids)
        ]
        if commit:
            self.db.commit()
        return created

    # -- reads ---------------------------------------------------------------
    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(
            stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total

    def unread_count(self, user_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
            or 0
        )

    def get(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = self.db.get(Notification, notification_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        if notification.user_id != user_id:
            raise PermissionDeniedError("Not your notification")
        return notification

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = self.get(notification_id, user_id)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(notification)
        return notification

    # -- typed event helpers (sports-aware) ---------------------------------
    def _find_by_event_key(
        self, user_id: uuid.UUID, event_key: str
    ) -> Notification | None:
        """Return an existing notification carrying ``event_key`` (idempotency)."""
        rows = self.db.scalars(
            select(Notification).where(Notification.user_id == user_id)
        ).all()
        for row in rows:
            if row.data and row.data.get("event_key") == event_key:
                return row
        return None

    def notify_activity_joined(
        self,
        *,
        host_id: uuid.UUID,
        joiner_id: uuid.UUID,
        activity_id: uuid.UUID,
        activity_title: str,
        sport_slug: str | None = None,
        waitlisted: bool = False,
        commit: bool = True,
    ) -> Notification:
        """Notify the host that someone joined (or waitlisted for) an activity."""
        verb = "waitlisted for" if waitlisted else "joined"
        return self.notify(
            host_id,
            type=NotificationType.JOIN_REQUEST,
            title=f"New participant {verb} your activity",
            body=f"A participant {verb} {activity_title!r}.",
            data={
                "activity_id": str(activity_id),
                "user_id": str(joiner_id),
                "sport_slug": sport_slug,
            },
            commit=commit,
            event_key=f"activity_joined:{activity_id}:{joiner_id}",
        )

    def notify_waitlist_promoted(
        self,
        *,
        user_id: uuid.UUID,
        activity_id: uuid.UUID,
        activity_title: str,
        sport_slug: str | None = None,
        commit: bool = True,
    ) -> Notification:
        """Notify a user they were promoted off the waitlist into the activity."""
        return self.notify(
            user_id,
            type=NotificationType.JOIN_REQUEST,
            title="You're off the waitlist",
            body=f"You were promoted from the waitlist for {activity_title!r}.",
            data={
                "activity_id": str(activity_id),
                "sport_slug": sport_slug,
                "promoted": True,
            },
            commit=commit,
            event_key=f"waitlist_promoted:{activity_id}:{user_id}",
        )

    def notify_booking_confirmed(
        self,
        *,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        sport_slug: str | None = None,
        commit: bool = True,
    ) -> Notification:
        """Notify a user their booking is confirmed."""
        return self.notify(
            user_id,
            type=NotificationType.BOOKING,
            title="Booking confirmed",
            body="Your booking is fully paid and confirmed.",
            data={"booking_id": str(booking_id), "sport_slug": sport_slug},
            commit=commit,
            event_key=f"booking_confirmed:{booking_id}",
        )

    def notify_payment_succeeded(
        self,
        *,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        payment_id: uuid.UUID,
        amount_cents: int,
        currency: str = "EUR",
        sport_slug: str | None = None,
        commit: bool = True,
    ) -> Notification:
        """Notify a user their payment was received."""
        return self.notify(
            user_id,
            type=NotificationType.PAYMENT,
            title="Payment received",
            body=f"Your payment of {amount_cents} {currency} was received.",
            data={
                "booking_id": str(booking_id),
                "payment_id": str(payment_id),
                "amount_cents": amount_cents,
                "currency": currency,
                "sport_slug": sport_slug,
            },
            commit=commit,
            event_key=f"payment_succeeded:{payment_id}",
        )

    def notify_checkin_recorded(
        self,
        *,
        user_id: uuid.UUID,
        activity_id: uuid.UUID,
        sport_slug: str | None = None,
        commit: bool = True,
    ) -> Notification:
        """Notify a user their check-in for an activity was recorded."""
        return self.notify(
            user_id,
            type=NotificationType.SYSTEM,
            title="Check-in recorded",
            body="Your attendance was recorded.",
            data={"activity_id": str(activity_id), "sport_slug": sport_slug},
            commit=commit,
            event_key=f"checkin_recorded:{activity_id}:{user_id}",
        )

    def notify_mmr_changed(
        self,
        *,
        user_id: uuid.UUID,
        delta: float,
        sport_slug: str | None = None,
        category: str | None = None,
        match_id: uuid.UUID | None = None,
        activity_id: uuid.UUID | None = None,
        commit: bool = True,
    ) -> Notification:
        """Notify a user their sport-specific MMR changed."""
        label = sport_slug or category or "your"
        sign = "+" if delta >= 0 else ""
        key_ref = match_id or activity_id or "na"
        return self.notify(
            user_id,
            type=NotificationType.MMR_UPDATE,
            title="MMR updated",
            body=f"Your {label} rating changed by {sign}{delta:.1f}.",
            data={
                "sport_slug": sport_slug,
                "category": category,
                "delta": round(delta, 2),
                "match_id": str(match_id) if match_id else None,
                "activity_id": str(activity_id) if activity_id else None,
            },
            commit=commit,
            event_key=f"mmr_changed:{key_ref}:{user_id}",
        )
