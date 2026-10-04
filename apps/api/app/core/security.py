"""Password hashing and JWT creation/verification.

Single source of truth for credential cryptography. Everything here is
server-side; the frontend never sees a password hash and never mints tokens.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt truncates at 72 bytes; we pass the secret through unchanged but the
# hashing scheme is fixed to bcrypt with a sane default work factor.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired or of the wrong type."""


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash for ``password``."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time check of a plaintext password against a stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Mint a short-lived access token for ``subject`` (the user id)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(str(subject), ACCESS_TOKEN_TYPE, delta, extra_claims)


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Mint a longer-lived refresh token for ``subject`` (the user id)."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(str(subject), REFRESH_TOKEN_TYPE, delta)


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT. Raises :class:`TokenError` on any problem."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError as exc:  # expired, bad signature, malformed...
        raise TokenError("invalid or expired token") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(f"expected {expected_type} token")

    if not payload.get("sub"):
        raise TokenError("token missing subject")

    return payload
