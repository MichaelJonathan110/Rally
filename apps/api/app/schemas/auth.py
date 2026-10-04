"""Authentication schemas: tokens and auth flows."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.passwords import validate_password

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Login by email OR username, plus password."""

    email: EmailStr | None = None
    username: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterResponse(BaseModel):
    user: UserRead
    tokens: TokenPair


class LoginResponse(BaseModel):
    user: UserRead
    tokens: TokenPair

class ForgotPasswordRequest(BaseModel):
    """Request a password-reset link. Always answered with 200 (no enumeration)."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password(v)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=8, max_length=512)


class MessageResponse(BaseModel):
    """Generic single-message envelope for auth side-effect endpoints."""

    message: str
