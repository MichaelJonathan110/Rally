"""Email + password-reset + email-verification flows.

Exercises the real FastAPI app against SQLite with the *outbox* email provider,
so every send writes a file we can read the raw token back from.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.user import User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
FORGOT = "/api/v1/auth/forgot-password"
RESET = "/api/v1/auth/reset-password"
VERIFY = "/api/v1/auth/verify-email"
RESEND = "/api/v1/auth/resend-verification"
ME = "/api/v1/auth/me"

CREDS = {"email": "alice@example.com", "username": "alice", "password": "Supersecret1"}
_TOKEN_RE = re.compile(r"token=([A-Za-z0-9_\-]+)")


@pytest.fixture()
def outbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings, "OUTBOX_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "outbox")
    return tmp_path


def _register(client: TestClient) -> dict:
    resp = client.post(REGISTER, json=CREDS)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _latest_token(outbox: Path, subject: str) -> str:
    files = sorted(outbox.glob("*.txt"))
    assert files, "no outbox file written"
    body = files[-1].read_text(encoding="utf-8")
    assert subject in body, body
    match = _TOKEN_RE.search(body)
    assert match, body
    return match.group(1)


def test_forgot_password_returns_200_and_writes_outbox(
    client: TestClient, outbox: Path
) -> None:
    _register(client)
    resp = client.post(FORGOT, json={"email": CREDS["email"]})
    assert resp.status_code == 200, resp.text
    files = list(outbox.glob("*.txt"))
    assert files, "expected an outbox email"
    assert any("Reset your password" in f.read_text(encoding="utf-8") for f in files)


def test_forgot_password_unknown_email_still_200(client: TestClient, outbox: Path) -> None:
    resp = client.post(FORGOT, json={"email": "nobody@example.com"})
    assert resp.status_code == 200
    assert not list(outbox.glob("*.txt")), "no email should be sent for unknown users"


def test_reset_password_changes_password(client: TestClient, outbox: Path) -> None:
    _register(client)
    client.post(FORGOT, json={"email": CREDS["email"]})
    token = _latest_token(outbox, "Reset your password")

    new_password = "BrandNew2Pass"
    resp = client.post(RESET, json={"token": token, "new_password": new_password})
    assert resp.status_code == 200, resp.text

    old = client.post(LOGIN, json={"email": CREDS["email"], "password": CREDS["password"]})
    assert old.status_code == 401
    new = client.post(LOGIN, json={"email": CREDS["email"], "password": new_password})
    assert new.status_code == 200, new.text


def test_reset_token_is_single_use(client: TestClient, outbox: Path) -> None:
    _register(client)
    client.post(FORGOT, json={"email": CREDS["email"]})
    token = _latest_token(outbox, "Reset your password")

    first = client.post(RESET, json={"token": token, "new_password": "BrandNew2Pass"})
    assert first.status_code == 200
    again = client.post(RESET, json={"token": token, "new_password": "Another3Pass"})
    assert again.status_code == 400


def test_reset_password_rejects_bad_token(client: TestClient, outbox: Path) -> None:
    _register(client)
    resp = client.post(RESET, json={"token": "not-a-real-token", "new_password": "BrandNew2Pass"})
    assert resp.status_code == 400


def test_verify_email_sets_flag(client: TestClient, outbox: Path, db_session) -> None:
    _register(client)
    token = _latest_token(outbox, "Verify your email")

    resp = client.post(VERIFY, json={"token": token})
    assert resp.status_code == 200, resp.text

    user = db_session.query(User).filter_by(email=CREDS["email"]).one()
    assert user.email_verified is True

    # reuse of the same token fails
    reuse = client.post(VERIFY, json={"token": token})
    assert reuse.status_code == 400


def test_resend_verification_requires_auth(client: TestClient, outbox: Path) -> None:
    _register(client)
    assert client.post(RESEND).status_code == 401

    login = client.post(LOGIN, json={"email": CREDS["email"], "password": CREDS["password"]})
    access = login.json()["tokens"]["access_token"]
    before = len(list(outbox.glob("*.txt")))
    resp = client.post(RESEND, headers={"Authorization": f"Bearer {access}"})
    assert resp.status_code == 200, resp.text
    assert len(list(outbox.glob("*.txt"))) > before


def test_me_includes_email_verified(client: TestClient, outbox: Path) -> None:
    body = _register(client)
    access = body["tokens"]["access_token"]
    me = client.get(ME, headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email_verified"] is False
