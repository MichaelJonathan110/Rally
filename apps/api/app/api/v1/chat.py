"""Chat endpoints: rooms, messages and a real-time WebSocket stream.

Membership is enforced for every REST call and for the WebSocket handshake; the
WS handler authenticates the JWT passed as a query parameter (browsers cannot set
headers on a WebSocket) and closes with 4401 (bad token) or 4403 (non-member).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import NotFoundError
from app.core.security import ACCESS_TOKEN_TYPE, TokenError, decode_token
from app.models.social import ChatMessage, ChatRoom
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessagePage,
    ChatMessageRead,
    ChatRoomPage,
    ChatRoomRead,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

DbSession = Annotated[Session, Depends(get_db)]

#: How many recent messages to replay to a client when it connects.
WS_BACKFILL_LIMIT = 20
#: WebSocket close codes.
WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403


class ConnectionManager:
    """In-process fan-out of room messages to connected WebSockets."""

    def __init__(self) -> None:
        self._rooms: dict[uuid.UUID, set[WebSocket]] = {}
        # The lock is (re)bound to the running event loop on first use so a
        # process that serves more than one loop (e.g. tests) stays safe.
        self._lock: asyncio.Lock | None = None
        self._lock_loop: object | None = None

    def _get_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        if self._lock is None or self._lock_loop is not loop:
            self._lock = asyncio.Lock()
            self._lock_loop = loop
        return self._lock

    async def connect(self, room_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._get_lock():
            self._rooms.setdefault(room_id, set()).add(websocket)

    async def disconnect(self, room_id: uuid.UUID, websocket: WebSocket) -> None:
        async with self._get_lock():
            clients = self._rooms.get(room_id)
            if clients is not None:
                clients.discard(websocket)
                if not clients:
                    self._rooms.pop(room_id, None)

    async def broadcast(self, room_id: uuid.UUID, payload: dict[str, object]) -> None:
        async with self._get_lock():
            clients = list(self._rooms.get(room_id, set()))
        dead: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_text(json.dumps(payload, default=str))
            except Exception:  # noqa: BLE001 - a broken socket must not stop the fan-out
                dead.append(client)
        for client in dead:
            await self.disconnect(room_id, client)


manager = ConnectionManager()


def _room_read(service: ChatService, room: ChatRoom) -> ChatRoomRead:
    return ChatRoomRead(
        id=room.id,
        type=room.type,
        name=room.name,
        activity_id=room.activity_id,
        club_id=room.club_id,
        last_message_at=service.last_message_at(room.id),
        unread_count=0,
        created_at=room.created_at,
    )


def _message_read(service: ChatService, message: ChatMessage) -> ChatMessageRead:
    return ChatMessageRead.model_validate(service.to_message_read(message))


@router.get("/rooms", response_model=ChatRoomPage)
def list_rooms(current_user: CurrentUser, db: DbSession) -> ChatRoomPage:
    """List the caller's chat rooms (newest first)."""
    service = ChatService(db)
    rooms = service.list_rooms_for_user(current_user.id)
    items = [_room_read(service, room) for room in rooms]
    return ChatRoomPage(items=items, total=len(items))


@router.get("/rooms/{room_id}", response_model=ChatRoomRead)
def get_room(room_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> ChatRoomRead:
    """Return one room; 404 if unknown, 403 if the caller is not a member."""
    service = ChatService(db)
    room = service.get_room(room_id)
    service.ensure_member(room, current_user.id)
    return _room_read(service, room)


@router.get("/rooms/{room_id}/messages", response_model=ChatMessagePage)
def list_messages(
    room_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ChatMessagePage:
    """List a room's messages (oldest first) for a member of that room."""
    service = ChatService(db)
    rows, total = service.list_messages(
        room_id, current_user.id, limit=limit, offset=offset
    )
    return ChatMessagePage(
        items=[_message_read(service, m) for m in rows], total=total
    )


@router.post(
    "/rooms/{room_id}/messages",
    response_model=ChatMessageRead,
    status_code=201,
)
def send_message(
    room_id: uuid.UUID,
    payload: ChatMessageCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ChatMessageRead:
    """Persist a message from the caller into a room they belong to."""
    service = ChatService(db)
    message = service.send_message(room_id, current_user.id, payload.body)
    return _message_read(service, message)


@router.websocket("/ws")
async def chat_ws(
    websocket: WebSocket,
    room_id: uuid.UUID,
    token: str,
    db: DbSession,
) -> None:
    """Authenticated, membership-checked real-time message stream for a room."""
    service = ChatService(db)

    try:
        claims = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
        user_id = uuid.UUID(claims["sub"])
    except (TokenError, KeyError, ValueError, TypeError):
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return

    try:
        room = service.get_room(room_id)
        service.ensure_member(room, user_id)
    except NotFoundError:
        await websocket.close(code=WS_CLOSE_FORBIDDEN)
        return
    except Exception:  # noqa: BLE001 - PermissionDeniedError -> non-member
        await websocket.close(code=WS_CLOSE_FORBIDDEN)
        return

    await manager.connect(room_id, websocket)
    try:
        for message in service.recent_messages(room_id, limit=WS_BACKFILL_LIMIT):
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "message",
                        "message": _message_read(service, message).model_dump(
                            mode="json"
                        ),
                    },
                    default=str,
                )
            )
        while True:
            data = await websocket.receive_json()
            body = (data or {}).get("body")
            if not isinstance(body, str) or not body.strip():
                continue
            message = service.send_message(room_id, user_id, body)
            await manager.broadcast(
                room_id,
                {
                    "type": "message",
                    "message": _message_read(service, message).model_dump(mode="json"),
                },
            )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(room_id, websocket)
