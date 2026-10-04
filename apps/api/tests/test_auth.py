"""Auth + RBAC contract tests.

Covers register, login, refresh and /auth/me end to end against the real
FastAPI app and a real (SQLite) database session, plus server-side
authorization: a valid token is required and roles are enforced by
dependencies, not the client.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.enums import UserRole
from app.models.user import User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/auth/me"

CREDS = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "Supersecret1",
}


def _register(client: TestClient, **overrides: str) -> dict:
    payload = {**CREDS, **overrides}
    resp = client.post(REGISTER, json=payload)
    return resp


def test_register_creates_user_and_returns_tokens(client: TestClient) -> None:
    resp = _register(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == CREDS["email"]
    assert body["user"]["username"] == CREDS["username"]
    assert "hashed_password" not in body["user"]
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"
    assert body["tokens"]["expires_in"] > 0


def test_register_first_user_becomes_admin(client: TestClient) -> None:
    body = _register(client).json()
    assert body["user"]["role"] == UserRole.ADMIN


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    assert _register(client).status_code == 201
    dup = _register(client, username="alice2")
    assert dup.status_code == 409


def test_register_rejects_weak_password(client: TestClient) -> None:
    resp = _register(client, password="short")
    assert resp.status_code == 422


def test_register_rejects_invalid_email(client: TestClient) -> None:
    resp = _register(client, email="not-an-email")
    assert resp.status_code == 422


def test_password_is_hashed_not_stored_plaintext(client: TestClient, db_session) -> None:
    _register(client)
    user = db_session.query(User).filter_by(email=CREDS["email"]).one()
    assert user.hashed_password != CREDS["password"]
    assert user.hashed_password.startswith("$2")


def test_login_with_email_succeeds(client: TestClient) -> None:
    _register(client)
    resp = client.post(LOGIN, json={"email": CREDS["email"], "password": CREDS["password"]})
    assert resp.status_code == 200, resp.text
    assert resp.json()["tokens"]["access_token"]


def test_login_with_username_succeeds(client: TestClient) -> None:
    _register(client)
    resp = client.post(
        LOGIN, json={"username": CREDS["username"], "password": CREDS["password"]}
    )
    assert resp.status_code == 200


def test_login_wrong_password_unauthorized(client: TestClient) -> None:
    _register(client)
    resp = client.post(LOGIN, json={"email": CREDS["email"], "password": "wrongpass1"})
    assert resp.status_code == 401


def test_login_unknown_user_unauthorized(client: TestClient) -> None:
    resp = client.post(LOGIN, json={"email": "ghost@example.com", "password": "whatever1"})
    assert resp.status_code == 401


def test_login_updates_last_login(client: TestClient, db_session) -> None:
    _register(client)
    client.post(LOGIN, json={"email": CREDS["email"], "password": CREDS["password"]})
    user = db_session.query(User).filter_by(email=CREDS["email"]).one()
    assert user.last_login_at is not None


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get(ME).status_code == 401


def test_me_rejects_garbage_token(client: TestClient) -> None:
    resp = client.get(ME, headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    tokens = _register(client).json()["tokens"]
    resp = client.get(ME, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == CREDS["email"]
    assert "hashed_password" not in body


def test_refresh_returns_new_token_pair(client: TestClient) -> None:
    tokens = _register(client).json()["tokens"]
    resp = client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200, resp.text
    new_tokens = resp.json()
    assert new_tokens["access_token"]
    # The refreshed access token must authenticate.
    me = client.get(ME, headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert me.status_code == 200


def test_access_token_cannot_be_used_as_refresh(client: TestClient) -> None:
    tokens = _register(client).json()["tokens"]
    resp = client.post(REFRESH, json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_refresh_with_invalid_token_unauthorized(client: TestClient) -> None:
    resp = client.post(REFRESH, json={"refresh_token": "garbage"})
    assert resp.status_code == 401


def test_token_for_unknown_user_is_rejected(client: TestClient) -> None:
    token = create_access_token("00000000-0000-0000-0000-000000000000")
    resp = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_inactive_user_cannot_authenticate(client: TestClient, db_session) -> None:
    _register(client)
    user = db_session.query(User).filter_by(email=CREDS["email"]).one()
    user.is_active = False
    db_session.add(user)
    db_session.commit()
    resp = client.post(LOGIN, json={"email": CREDS["email"], "password": CREDS["password"]})
    assert resp.status_code == 403


# --- RBAC: roles are enforced server-side by dependencies -------------------


def test_require_roles_grants_matching_role() -> None:
    from app.api.deps import require_roles

    user = User(id=None, email="h@example.com", username="host", hashed_password="x",
                role=UserRole.HOST)
    assert require_roles(UserRole.HOST)(user) is user


def test_require_roles_rejects_wrong_role() -> None:
    from fastapi import HTTPException

    from app.api.deps import require_roles

    user = User(id=None, email="u@example.com", username="user", hashed_password="x",
                role=UserRole.USER)
    with pytest.raises(HTTPException) as exc:
        require_roles(UserRole.MODERATOR, UserRole.ADMIN)(user)
    assert exc.value.status_code == 403


def test_require_roles_admin_bypasses_gate() -> None:
    from app.api.deps import require_roles

    admin = User(id=None, email="a@example.com", username="admin", hashed_password="x",
                 role=UserRole.ADMIN)
    assert require_roles(UserRole.VENUE_MANAGER)(admin) is admin
