"""Single-use, expiring tokens for email verification and password reset.

Only a SHA-256 *hash* of the raw token is stored, so a database leak does not
expose usable links. The raw token lives only in the email sent to the user.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

EMAIL_VERIFY = "email_verify"
PASSWORD_RESET = "password_reset"


class OneTimeToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A hashed, single-use, expiring token tied to a user and a purpose."""

    __tablename__ = "one_time_tokens"
    __table_args__ = (
        Index("ix_one_time_tokens_token_hash", "token_hash"),
        Index("ix_one_time_tokens_user_kind", "user_id", "kind"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
