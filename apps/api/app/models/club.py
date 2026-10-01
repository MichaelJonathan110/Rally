"""Club and ClubMember models."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ActivityCategory, UserRole, pg_enum


class Club(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clubs"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_clubs_slug"),
    )

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
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    members: Mapped[list[ClubMember]] = relationship(
        back_populates="club", cascade="all, delete-orphan"
    )


class ClubMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "club_members"
    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_club_members_club_user"),
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
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "userrole"), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    club: Mapped[Club] = relationship(back_populates="members")
