"""Notification schemas (in-app channel)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.models.enums import NotificationType
from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    body: str | None = None
    data: dict[str, Any] | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationPage(ORMModel):
    items: list[NotificationRead]
    total: int
    unread_count: int
