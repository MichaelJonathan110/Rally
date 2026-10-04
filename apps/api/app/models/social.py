"""Social + moderation models.

ChatRoom, ChatMessage, CheckIn, Notification, Review, Achievement,
UserAchievement, Report and ModerationAction.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ChatRoomType,
    MessageType,
    ModerationActionType,
    NotificationType,
    ReportStatus,
    ReportTargetType,
    ReviewTargetType,
    pg_enum,
)


class ChatRoom(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_rooms"

    type: Mapped[ChatRoomType] = mapped_column(
        pg_enum(ChatRoomType, "chatroomtype"),
        default=ChatRoomType.GROUP,
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(120))
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), index=True
    )
    club_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), index=True
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    room_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[MessageType] = mapped_column(
        pg_enum(MessageType, "messagetype"), default=MessageType.TEXT, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(512))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    room: Mapped[ChatRoom] = relationship(back_populates="messages")


class CheckIn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user checking in to an activity (idempotent per activity and user)."""

    __tablename__ = "check_ins"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_check_ins_activity_user"),
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()
    method: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        pg_enum(NotificationType, "notificationtype"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict[str, object] | None] = mapped_column(JSON)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "author_id", "target_type", "target_id", name="uq_reviews_author_target"
        ),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[ReviewTargetType] = mapped_column(
        pg_enum(ReviewTargetType, "reviewtargettype"), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Achievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("code", name="uq_achievements_code"),)

    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(60))
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserAchievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievements_user_ach"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    earned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    reporter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[ReportTargetType] = mapped_column(
        pg_enum(ReportTargetType, "reporttargettype"), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ReportStatus] = mapped_column(
        pg_enum(ReportStatus, "reportstatus"),
        default=ReportStatus.OPEN,
        nullable=False,
        index=True,
    )
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    actions: Mapped[list[ModerationAction]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ModerationAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "moderation_actions"

    report_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("reports.id", ondelete="SET NULL"), index=True
    )
    moderator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[ModerationActionType] = mapped_column(
        pg_enum(ModerationActionType, "moderationactiontype"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, object] | None] = mapped_column("metadata", JSON)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    report: Mapped[Report | None] = relationship(back_populates="actions")
