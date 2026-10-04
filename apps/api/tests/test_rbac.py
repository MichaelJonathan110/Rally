"""End-to-end RBAC tests: role gates are enforced by server dependencies.

A second (non-admin) user is created through the real registration endpoint and
then attempts to reach admin-only routes. The 403 must come from the server
dependency, regardless of any client-side state.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User

REGISTER = "/api/v1/auth/register"
ADMIN_PING = "/api/v1/admin/ping"
ADMIN_USERS = "/api/v1/admin/users"


def _make_user(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER, json={"email": email, "username": username, "password": "RallyPass123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_admin_ping_requires_auth(client: TestClient) -> None:
    assert client.get(ADMIN_PING).status_code == 401


def test_normal_user_forbidden_on_admin_route(client: TestClient) -> None:
    admin = _make_user(client, "admin@example.com", "admin")
    assert admin["user"]["role"] == UserRole.ADMIN
    member = _make_user(client, "member@example.com", "member")
    assert member["user"]["role"] == UserRole.USER

    resp = client.get(ADMIN_PING, headers=_auth(member["tokens"]))
    assert resp.status_code == 403


def test_admin_allowed_on_admin_route(client: TestClient) -> None:
    admin = _make_user(client, "admin2@example.com", "admin2")
    resp = client.get(ADMIN_PING, headers=_auth(admin["tokens"]))
    assert resp.status_code == 200
    assert resp.json() == {"status": "admin_ok"}


def test_moderator_allowed_on_users_but_not_admin_ping(
    client: TestClient, db_session: Session
) -> None:
    _make_user(client, "admin3@example.com", "admin3")
    mod = _make_user(client, "mod@example.com", "mod")
    user = db_session.query(User).filter_by(email="mod@example.com").one()
    user.role = UserRole.MODERATOR
    db_session.add(user)
    db_session.commit()

    # Re-login so the token reflects the elevated role (role is a claim).
    login = client.post(
        "/api/v1/auth/login", json={"email": "mod@example.com", "password": "RallyPass123"}
    )
    headers = _auth(login.json()["tokens"])

    assert client.get(ADMIN_USERS, headers=headers).status_code == 200
    assert client.get(ADMIN_PING, headers=headers).status_code == 403
