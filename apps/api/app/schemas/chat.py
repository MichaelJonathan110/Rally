"""Chat schemas: rooms and messages."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ChatRoomType


class ChatRoomRead(BaseModel):
    """A chat room as seen by a member (unread_count may be 0 for now)."""

    id: uuid.UUID
    type: ChatRoomType
    name: str | None = None
    activity_id: uuid.UUID | None = None
    club_id: uuid.UUID | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    created_at: datetime


class ChatMessageRead(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str | None = None
    body: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ChatRoomPage(BaseModel):
    items: list[ChatRoomRead]
    total: int


class ChatMessagePage(BaseModel):
    items: list[ChatMessageRead]
    total: int
