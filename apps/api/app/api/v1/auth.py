"""Authentication endpoints: register, login, refresh and current user."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.config import settings
from app.core.rate_limit import auth_limiter
from app.core.security import (
    REFRESH_TOKEN_TYPE,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.models.user import Profile, User
from app.models.token import EMAIL_VERIFY, PASSWORD_RESET
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserRead
from app.services.email_service import render_action_email, send_email
from app.services.token_service import TokenInvalidError, TokenService

logger = logging.getLogger("rally.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


def _client_ip(request: Request) -> str:
    """Best-effort client IP for rate-limit keying (honours X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request, scope: str) -> None:
    """Token-bucket gate for auth endpoints; raises 429 when exhausted."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    key = f"{scope}:{_client_ip(request)}"
    if not auth_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests; please slow down and try again shortly",
            headers={"Retry-After": "60"},
        )


def _send_verification_email(db: Session, user: User) -> None:
    """Best-effort verification email; never raises into the request."""
    try:
        raw = TokenService(db).issue(user.id, EMAIL_VERIFY)
        link = f"{settings.FRONTEND_BASE_URL}/verify-email?token={raw}"
        text, html = render_action_email(
            to=user.email,
            subject="Verify your email",
            link=link,
            intro="Welcome to RALLY! Confirm your email address to activate your account.",
            cta="Verify email",
        )
        send_email(user.email, "Verify your email", html, text)
    except Exception:  # noqa: BLE001 - registration must not fail on email issues
        logger.exception("failed to send verification email to %s", user.email)


def _issue_tokens(user: User) -> TokenPair:
    """Mint an access/refresh pair carrying the user's role as a claim."""
    claims = {"role": str(user.role)}
    access = create_access_token(user.id, extra_claims=claims)
    refresh = create_refresh_token(user.id)
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: UserCreate, db: DbSession, request: Request) -> RegisterResponse:
    """Create a new account and return it with a fresh token pair.

    The very first registered account is promoted to ADMIN so a fresh install
    is administrable; everyone else is a normal USER.
    """
    _enforce_rate_limit(request, "register")
    existing = db.scalar(
        select(User).where(
            or_(User.email == payload.email, User.username == payload.username)
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already registered",
        )

    is_first_user = db.scalar(select(func.count()).select_from(User)) == 0
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN if is_first_user else UserRole.USER,
        is_active=True,
    )
    user.profile = Profile(display_name=payload.username)
    db.add(user)
    db.commit()
    db.refresh(user)

    _send_verification_email(db, user)

    return RegisterResponse(user=UserRead.model_validate(user), tokens=_issue_tokens(user))


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DbSession, request: Request) -> LoginResponse:
    """Authenticate with email or username plus password."""
    _enforce_rate_limit(request, "login")
    if not payload.email and not payload.username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either email or username",
        )

    identifier = payload.email or payload.username
    user = db.scalar(
        select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
    )
    # Same generic error whether the user is unknown or the password is wrong.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)

    return LoginResponse(user=UserRead.model_validate(user), tokens=_issue_tokens(user))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession, request: Request) -> TokenPair:
    """Exchange a valid refresh token for a new token pair."""
    _enforce_rate_limit(request, "refresh")
    try:
        claims = decode_token(payload.refresh_token, expected_type=REFRESH_TOKEN_TYPE)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    try:
        user_id = uuid.UUID(claims["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token subject",
        ) from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer valid"
        )
    return _issue_tokens(user)


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> UserRead:
    """Return the authenticated caller's own record (requires a valid token)."""
    return UserRead.model_validate(current_user)

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: DbSession, request: Request
) -> MessageResponse:
    """Request a reset link. Always 200 - never reveals whether the email exists."""
    _enforce_rate_limit(request, "forgot_password")
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is not None and user.is_active:
        try:
            raw = TokenService(db).issue(user.id, PASSWORD_RESET)
            link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={raw}"
            text, html = render_action_email(
                to=user.email,
                subject="Reset your password",
                link=link,
                intro="We received a request to reset your RALLY password.",
                cta="Reset password",
            )
            send_email(user.email, "Reset your password", html, text)
        except Exception:  # noqa: BLE001 - never leak failures via the response
            logger.exception("failed to issue reset token for %s", user.email)
    return MessageResponse(
        message="If that email is registered, a reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> MessageResponse:
    """Consume a reset token and set a new password."""
    try:
        row = TokenService(db).consume(payload.token, PASSWORD_RESET)
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from None
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    return MessageResponse(message="Password has been reset.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> MessageResponse:
    """Consume a verification token and mark the account's email verified."""
    try:
        row = TokenService(db).consume(payload.token, EMAIL_VERIFY)
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        ) from None
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    user.email_verified = True
    db.add(user)
    db.commit()
    return MessageResponse(message="Email verified.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(current_user: CurrentUser, db: DbSession) -> MessageResponse:
    """Re-send the verification email for the authenticated caller."""
    if not current_user.email_verified:
        _send_verification_email(db, current_user)
    return MessageResponse(message="Verification email sent.")
