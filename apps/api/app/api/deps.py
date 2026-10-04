"""Shared FastAPI dependencies: DB session, authentication and RBAC.

Authorization is enforced here, in the request pipeline - never trusted to the
client. Endpoints declare the roles they require and the dependency rejects
unauthorised callers before the handler runs.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ACCESS_TOKEN_TYPE, TokenError, decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

# auto_error=False so we can raise a consistent 401 with WWW-Authenticate.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def get_session(db: Annotated[Session, Depends(get_db)]) -> Session:
    """Alias dependency so routers can depend on ``get_session``."""
    return db


_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the authenticated user from a bearer access token.

    Raises 401 for a missing/invalid token and 403 for a disabled account.
    """
    if not token:
        raise _CREDENTIALS_EXC
    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
    except TokenError:
        raise _CREDENTIALS_EXC from None

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        raise _CREDENTIALS_EXC from None

    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_EXC
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(user: CurrentUser) -> User:
    """Explicit alias; ``get_current_user`` already enforces ``is_active``."""
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the caller holds one of ``roles``.

    Usage::

        @router.get("/admin", dependencies=[Depends(require_roles(UserRole.ADMIN))])

    Admins are implicitly allowed through every role gate.
    """
    allowed = set(roles)

    def _checker(user: CurrentUser) -> User:
        if user.role == UserRole.ADMIN or user.role in allowed:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this resource",
        )

    return _checker


def require_admin(user: CurrentUser) -> User:
    """Convenience dependency for admin-only endpoints."""
    return require_roles(UserRole.ADMIN)(user)
