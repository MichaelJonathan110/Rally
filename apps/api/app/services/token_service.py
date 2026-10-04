"""Single-use token issuance and verification (email verify / password reset).

Raw tokens are generated with :mod:`secrets`, returned once to the caller (to be
emailed) and stored only as a SHA-256 hash. Verification hashes the presented
token and looks it up; a token is valid only if it exists, is unused and is not
expired. Consuming a token marks ``used_at``; issuing a new token of a kind
invalidates the user's outstanding tokens of that kind.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.token import EMAIL_VERIFY, PASSWORD_RESET, OneTimeToken


class TokenInvalidError(Exception):
    """Raised when a presented token is unknown, used or expired."""


def hash_token(raw: str) -> str:
    """Return the hex SHA-256 digest used for storage/lookup."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ttl(kind: str) -> timedelta:
    if kind == PASSWORD_RESET:
        return timedelta(hours=settings.PASSWORD_RESET_TTL_HOURS)
    return timedelta(hours=settings.EMAIL_VERIFY_TTL_HOURS)


class TokenService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def issue(self, user_id: uuid.UUID, kind: str, *, commit: bool = True) -> str:
        """Invalidate outstanding tokens of ``kind`` and mint a fresh one.

        Returns the RAW token (only the hash is persisted).
        """
        now = datetime.now(UTC)
        self.db.execute(
            update(OneTimeToken)
            .where(
                OneTimeToken.user_id == user_id,
                OneTimeToken.kind == kind,
                OneTimeToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        raw = secrets.token_urlsafe(32)
        row = OneTimeToken(
            user_id=user_id,
            kind=kind,
            token_hash=hash_token(raw),
            expires_at=now + _ttl(kind),
        )
        self.db.add(row)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return raw

    def consume(self, raw: str, kind: str, *, commit: bool = True) -> OneTimeToken:
        """Validate ``raw`` for ``kind`` and mark it used. Raises on any problem."""
        row = self.db.scalar(
            select(OneTimeToken).where(
                OneTimeToken.token_hash == hash_token(raw),
                OneTimeToken.kind == kind,
            )
        )
        if row is None:
            raise TokenInvalidError("Invalid token")
        if row.used_at is not None:
            raise TokenInvalidError("Token already used")
        now = datetime.now(UTC)
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < now:
            raise TokenInvalidError("Token expired")
        row.used_at = now
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row
