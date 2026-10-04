"""Chat business logic: rooms, membership and messages.

Rooms are derived containers: an activity room is visible to that activity's
participants, a club room to the club's active members. Membership is always
recomputed server-side from the domain tables, never trusted from the client.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.activity import ActivityParticipant
from app.models.club import ClubMember
from app.models.enums import ChatRoomType, ParticipantStatus
from app.models.social import ChatMessage, ChatRoom
from app.models.tournament import TournamentEntry
from app.models.user import User

# Participant statuses that grant access to an activity room.
_ACTIVE_PARTICIPANT_STATUSES = (
    ParticipantStatus.CONFIRMED,
    ParticipantStatus.ATTENDED,
    ParticipantStatus.WAITLISTED,
)


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_room(
        self,
        *,
        activity_id: uuid.UUID | None = None,
        club_id: uuid.UUID | None = None,
        tournament_id: uuid.UUID | None = None,
        name: str | None = None,
        created_by_id: uuid.UUID | None = None,
    ) -> ChatRoom:
        """Return the room bound to the given scope, creating it lazily."""
        stmt = select(ChatRoom)
        if activity_id is not None:
            stmt = stmt.where(ChatRoom.activity_id == activity_id)
            room_type = ChatRoomType.ACTIVITY
        elif club_id is not None:
            stmt = stmt.where(ChatRoom.club_id == club_id)
            room_type = ChatRoomType.CLUB
        elif tournament_id is not None:
            stmt = stmt.where(ChatRoom.tournament_id == tournament_id)
            room_type = ChatRoomType.TOURNAMENT
        else:
            raise PermissionDeniedError(
                "A room must be scoped to an activity, club or tournament"
            )

        existing = self.db.scalars(stmt).first()
        if existing is not None:
            return existing

        room = ChatRoom(
            type=room_type,
            name=name,
            activity_id=activity_id,
            club_id=club_id,
            tournament_id=tournament_id,
            created_by_id=created_by_id,
        )
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def get_room(self, room_id: uuid.UUID) -> ChatRoom:
        room = self.db.get(ChatRoom, room_id)
        if room is None:
            raise NotFoundError("Chat room not found")
        return room

    def is_member(self, room: ChatRoom, user_id: uuid.UUID) -> bool:
        if room.activity_id is not None:
            return (
                self.db.scalar(
                    select(func.count())
                    .select_from(ActivityParticipant)
                    .where(
                        ActivityParticipant.activity_id == room.activity_id,
                        ActivityParticipant.user_id == user_id,
                        ActivityParticipant.status.in_(_ACTIVE_PARTICIPANT_STATUSES),
                    )
                )
                or 0
            ) > 0
        if room.club_id is not None:
            return (
                self.db.scalar(
                    select(func.count())
                    .select_from(ClubMember)
                    .where(
                        ClubMember.club_id == room.club_id,
                        ClubMember.user_id == user_id,
                        ClubMember.is_active.is_(True),
                    )
                )
                or 0
            ) > 0
        if room.tournament_id is not None:
            return (
                self.db.scalar(
                    select(func.count())
                    .select_from(TournamentEntry)
                    .where(
                        TournamentEntry.tournament_id == room.tournament_id,
                        TournamentEntry.user_id == user_id,
                    )
                )
                or 0
            ) > 0
        return room.created_by_id == user_id

    def ensure_member(self, room: ChatRoom, user_id: uuid.UUID) -> None:
        if not self.is_member(room, user_id):
            raise PermissionDeniedError("You are not a member of this chat room")

    def list_rooms_for_user(self, user_id: uuid.UUID) -> list[ChatRoom]:
        """Rooms the user may see (activity rooms they participate in, clubs).

        Rooms are materialised lazily: joining an activity or club makes its
        room appear on the next read without an explicit create call.
        """
        activity_ids = select(ActivityParticipant.activity_id).where(
            ActivityParticipant.user_id == user_id,
            ActivityParticipant.status.in_(_ACTIVE_PARTICIPANT_STATUSES),
        )
        club_ids = select(ClubMember.club_id).where(
            ClubMember.user_id == user_id, ClubMember.is_active.is_(True)
        )
        tournament_ids = select(TournamentEntry.tournament_id).where(
            TournamentEntry.user_id == user_id
        )
        self._ensure_rooms_for_scopes(activity_ids, club_ids, tournament_ids, user_id)
        rows = self.db.scalars(
            select(ChatRoom)
            .where(
                ChatRoom.is_archived.is_(False),
                (ChatRoom.activity_id.in_(activity_ids))
                | (ChatRoom.club_id.in_(club_ids))
                | (ChatRoom.tournament_id.in_(tournament_ids))
                | (ChatRoom.created_by_id == user_id),
            )
            .order_by(ChatRoom.created_at.desc())
        ).all()
        return list(rows)

    def _ensure_rooms_for_scopes(
        self,
        activity_ids: object,
        club_ids: object,
        tournament_ids: object,
        user_id: uuid.UUID,
    ) -> None:
        """Create any missing rooms for the scopes the user belongs to."""
        for activity_id in self.db.scalars(activity_ids).all():
            self.ensure_room(activity_id=activity_id)
        for club_id in self.db.scalars(club_ids).all():
            self.ensure_room(club_id=club_id)
        for tournament_id in self.db.scalars(tournament_ids).all():
            self.ensure_room(tournament_id=tournament_id)

    def last_message_at(self, room_id: uuid.UUID) -> datetime | None:
        return self.db.scalar(
            select(func.max(ChatMessage.created_at)).where(ChatMessage.room_id == room_id)
        )

    def list_messages(
        self, room_id: uuid.UUID, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[ChatMessage], int]:
        room = self.get_room(room_id)
        self.ensure_member(room, user_id)
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id, ChatMessage.is_deleted.is_(False))
            .order_by(ChatMessage.created_at.asc())
        )
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(stmt.limit(limit).offset(offset)).all()
        return list(rows), total

    def recent_messages(self, room_id: uuid.UUID, *, limit: int = 20) -> list[ChatMessage]:
        """Newest limit messages in chronological order (WS backfill)."""
        rows = self.db.scalars(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id, ChatMessage.is_deleted.is_(False))
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        ).all()
        return list(reversed(list(rows)))

    def send_message(
        self, room_id: uuid.UUID, sender_id: uuid.UUID, body: str
    ) -> ChatMessage:
        room = self.get_room(room_id)
        self.ensure_member(room, sender_id)
        message = ChatMessage(room_id=room_id, sender_id=sender_id, body=body)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def sender_name(self, user_id: uuid.UUID) -> str | None:
        user = self.db.get(User, user_id)
        return user.username if user is not None else None

    def to_message_read(self, message: ChatMessage) -> dict[str, object]:
        return {
            "id": message.id,
            "room_id": message.room_id,
            "sender_id": message.sender_id,
            "sender_name": self.sender_name(message.sender_id),
            "body": message.body,
            "created_at": message.created_at,
        }
