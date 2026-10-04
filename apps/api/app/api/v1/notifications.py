"""Notification endpoints (in-app channel).

Notifications are created by the domain (join, booking, payment, cancellation);
these routes let a user read their own inbox and mark items read.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.schemas.notification import NotificationPage, NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=NotificationPage)
def list_notifications(
    current_user: CurrentUser,
    db: DbSession,
    unread_only: bool = False,
    unread: bool | None = Query(default=None, description="Only unread when true"),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NotificationPage:
    """List the caller's notifications (newest first).

    Filter with either ``?unread_only=true`` or the ``?unread=true`` alias. The
    payload exposes the sport slug (when known) inside each item's ``data``.
    """
    service = NotificationService(db)
    only_unread = unread_only or bool(unread)
    rows, total = service.list_for_user(
        current_user.id, unread_only=only_unread, limit=limit, offset=offset
    )
    return NotificationPage(
        items=[NotificationRead.model_validate(n) for n in rows],
        total=total,
        unread_count=service.unread_count(current_user.id),
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> NotificationRead:
    """Mark one of the caller's notifications as read (idempotent)."""
    notification = NotificationService(db).mark_read(notification_id, current_user.id)
    return NotificationRead.model_validate(notification)
