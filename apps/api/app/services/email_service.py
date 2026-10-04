"""Transactional email with a swappable provider.

Providers (``settings.EMAIL_PROVIDER``):

* ``outbox`` (default) - render the email and write it to
  ``<OUTBOX_DIR>/<timestamp>-<slug>.eml`` plus a sibling ``.txt``; logs the path.
  Used in dev/tests so no SMTP server is required.
* ``console`` - log the rendered email to stdout/logger.
* ``smtp`` - send via :mod:`smtplib` using ``SMTP_HOST``/``SMTP_PORT``/
  ``SMTP_USER``/``SMTP_PASSWORD``/``SMTP_TLS`` and ``EMAIL_FROM``.

``send_email`` is best-effort: any failure is logged and swallowed so an email
problem NEVER breaks the surrounding request.
"""
from __future__ import annotations

import logging
import re
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Protocol

from app.core.config import settings

NL = chr(10)

logger = logging.getLogger("rally.email")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")[:60] or "email"


def render_action_email(
    *, to: str, subject: str, link: str, intro: str, cta: str
) -> tuple[str, str]:
    """Return ``(body_text, body_html)`` for a single-action email."""
    body_text = (
        intro + NL + NL + cta + ": " + link + NL + NL
        + "If you didn't request this, you can safely ignore this email." + NL
    )
    body_html = (
        "<p>" + intro + "</p>"
        + '<p><a href="' + link + '">' + cta + "</a></p>"
        + "<p>Or paste this link into your browser:<br><code>" + link + "</code></p>"
        + "<p>If you didn't request this, you can safely ignore this email.</p>"
    )
    return body_text, body_html


class EmailProvider(Protocol):
    name: str

    def deliver(self, *, to: str, subject: str, body_html: str, body_text: str) -> None:
        ...


class OutboxProvider:
    """Writes the email to disk under ``OUTBOX_DIR`` and logs the path."""

    name = "outbox"

    def __init__(self, outbox_dir: str | None = None) -> None:
        base = Path(outbox_dir or settings.OUTBOX_DIR)
        if not base.is_absolute():
            base = Path.cwd() / base
        self.dir = base

    def deliver(self, *, to: str, subject: str, body_html: str, body_text: str) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        stem = f"{stamp}-{_slug(to)}-{_slug(subject)}"
        txt_path = self.dir / f"{stem}.txt"
        eml_path = self.dir / f"{stem}.eml"
        txt_path.write_text(
            "To: " + to + NL + "Subject: " + subject + NL + NL + body_text,
            encoding="utf-8",
        )
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body_text)
        message.add_alternative(body_html, subtype="html")
        eml_path.write_bytes(message.as_bytes())
        logger.info("email[outbox] to=%s subject=%r path=%s", to, subject, txt_path)


class ConsoleProvider:
    """Logs the rendered email; nothing is transmitted."""

    name = "console"

    def deliver(self, *, to: str, subject: str, body_html: str, body_text: str) -> None:
        logger.info(
            "email[console] to=%s subject=%s body=%s", to, subject, body_text
        )


class SmtpProvider:
    """Sends via SMTP (STARTTLS by default) using settings.SMTP_*."""

    name = "smtp"

    def deliver(self, *, to: str, subject: str, body_html: str, body_text: str) -> None:
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body_text)
        message.add_alternative(body_html, subtype="html")

        host = settings.SMTP_HOST
        if not host:
            raise RuntimeError("SMTP_HOST is not configured")
        with smtplib.SMTP(host, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls(context=ssl.create_default_context())
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            smtp.send_message(message)
        logger.info("email[smtp] to=%s subject=%r", to, subject)


def get_provider() -> EmailProvider:
    """Resolve the configured provider (defaults to outbox)."""
    name = (settings.EMAIL_PROVIDER or "outbox").lower()
    if name == "smtp":
        return SmtpProvider()
    if name == "console":
        return ConsoleProvider()
    return OutboxProvider()


def send_email(
    to: str,
    subject: str,
    body_html: str,
    body_text: str,
    *,
    provider: EmailProvider | None = None,
) -> bool:
    """Best-effort send. Returns ``True`` on success, ``False`` on failure.

    Never raises: email delivery must not break the caller's request.
    """
    active = provider or get_provider()
    try:
        active.deliver(to=to, subject=subject, body_html=body_html, body_text=body_text)
        return True
    except Exception:  # noqa: BLE001 - email must never crash the request
        logger.exception("email delivery failed (provider=%s to=%s)", active.name, to)
        return False
