"""Input sanitisation helpers.

We do not rewrite user text (that corrupts legitimate content and is the job of
output encoding), but we DO strip control characters and reject payloads that
are obviously abusive (HTML/script tags, null bytes). Combined with Pydantic
length limits this closes the cheap injection/DoS surface without a heavy
dependency.
"""
from __future__ import annotations

import re

# Control chars except tab/newline/carriage-return.
_CONTROL_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TAG_LIKE = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
_SCRIPT_LIKE = re.compile(r"(javascript:|<script|onerror\s*=|onload\s*=)", re.IGNORECASE)


def strip_control_chars(value: str) -> str:
    """Remove NUL and other non-printable control characters."""
    return _CONTROL_CHARS.sub("", value)


def clean_text(value: str, *, max_length: int | None = None) -> str:
    """Normalise free text: strip control chars, trim, and reject markup.

    Raises ValueError if the value still looks like an injection attempt
    (HTML/script) so Pydantic surfaces a clean 422.
    """
    cleaned = strip_control_chars(value).strip()
    if _SCRIPT_LIKE.search(cleaned):
        raise ValueError("Input contains disallowed markup")
    if max_length is not None and len(cleaned) > max_length:
        raise ValueError(f"Input exceeds {max_length} characters")
    return cleaned


def looks_like_markup(value: str) -> bool:
    """True when value contains HTML-tag-like or script-like content."""
    return bool(_TAG_LIKE.search(value) or _SCRIPT_LIKE.search(value))
