"""Club, ClubMember and ClubJoinRequest models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    ActivityCategory,
    ClubJoinRequestStatus,
    SportCategory,
    UserRole,
    pg_enum,
)


class Club(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clubs"
    __table_args__ = (UniqueConstraint("slug", name="uq_clubs_slug"),)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[ActivityCategory] = mapped_column(
        pg_enum(ActivityCategory, "activitycategory"), nullable=False, index=True
    )
    #: SPORT slug from :mod:`app.core.sports` (e.g. padel, running).
    #: Nullable so rows created before the sports pivot stay valid.
    sport_slug: Mapped[str | None] = mapped_column(String(40), index=True)
    #: Sport category derived from ``sport_slug`` (racket/team/combat/...).
    sport_category: Mapped[SportCategory | None] = mapped_column(
        pg_enum(SportCategory, "sportcategory"), index=True
    )
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    members: Mapped[list[ClubMember]] = relationship(
        back_populates="club", cascade="all, delete-orphan"
    )
    join_requests: Mapped[list[ClubJoinRequest]] = relationship(
        back_populates="club", cascade="all, delete-orphan"
    )


class ClubMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_members"
    __table_args__ = (UniqueConstraint("club_id", "user_id", name="uq_club_members_club_user"),)

    club_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "userrole"), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    club: Mapped[Club] = relationship(back_populates="members")


class ClubJoinRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A pending request to join a (typically private) club."""

    __tablename__ = "club_join_requests"
    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_join_requests_club_user"),
    )

    club_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ClubJoinRequestStatus] = mapped_column(
        pg_enum(ClubJoinRequestStatus, "clubjoinrequeststatus"),
        default=ClubJoinRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    message: Mapped[str | None] = mapped_column(Text)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    club: Mapped[Club] = relationship(back_populates="join_requests")
