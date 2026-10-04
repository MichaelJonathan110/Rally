"""Password strength validation.

Deliberately dependency-free. Rejects the passwords attackers try first
(too-short, all-one-class, common strings) and returns actionable messages so
the 422 body tells the user exactly what to fix.
"""
from __future__ import annotations

from app.core.config import settings

_COMMON_PASSWORDS = {
    "password", "password1", "password123", "12345678", "123456789",
    "qwertyui", "qwerty123", "letmein", "iloveyou", "admin123",
    "welcome1", "monkey123", "dragon123", "football", "baseball",
}


def validate_password(password: str) -> str:
    """Return the password if strong enough, else raise ValueError.

    Rules: >= MIN_PASSWORD_LENGTH chars, at least three of {lower, upper,
    digit, symbol}, and not a well-known common password.
    """
    min_len = settings.MIN_PASSWORD_LENGTH
    if len(password) < min_len:
        raise ValueError(f"Password must be at least {min_len} characters long")
    if password.lower() in _COMMON_PASSWORDS:
        raise ValueError("Password is too common; choose something less guessable")

    classes = 0
    if any(c.islower() for c in password):
        classes += 1
    if any(c.isupper() for c in password):
        classes += 1
    if any(c.isdigit() for c in password):
        classes += 1
    if any(not c.isalnum() for c in password):
        classes += 1
    if classes < 3:
        raise ValueError(
            "Password must mix at least three of: lowercase, uppercase, digits, symbols"
        )
    return password
