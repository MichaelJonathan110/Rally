"""Admin/moderation tests: RBAC gates, role changes, ban/unban and the log.

The first registered account is promoted to ADMIN by the app, so it is used as
the privileged actor. A second user proves the 403 path.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ADMIN_USERS = "/api/v1/admin/users"
ADMIN_ACTIONS = "/api/v1/admin/moderation-actions"


def _make_user(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER, json={"email": email, "username": username, "password": "RallyPass123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_admin_required_for_user_list(client: TestClient) -> None:
    _make_user(client, "admin@example.com", "admin")
    member = _make_user(client, "member@example.com", "member")
    resp = client.get(ADMIN_USERS, headers=_auth(member["tokens"]))
    assert resp.status_code == 403


def test_admin_can_list_users(client: TestClient) -> None:
    admin = _make_user(client, "admin2@example.com", "admin2")
    resp = client.get(ADMIN_USERS, headers=_auth(admin["tokens"]))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_change_role_admin_only_and_logged(client: TestClient) -> None:
    admin = _make_user(client, "admin3@example.com", "admin3")
    member = _make_user(client, "promote@example.com", "promote")
    target_id = member["user"]["id"]

    # Non-admin cannot change roles.
    resp = client.patch(
        f"{ADMIN_USERS}/{target_id}/role",
        headers=_auth(member["tokens"]),
        json={"role": "moderator"},
    )
    assert resp.status_code == 403

    # Admin can.
    resp = client.patch(
        f"{ADMIN_USERS}/{target_id}/role",
        headers=_auth(admin["tokens"]),
        json={"role": "moderator"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "moderator"

    # The action was written to the audit log.
    log = client.get(ADMIN_ACTIONS, headers=_auth(admin["tokens"]))
    assert log.status_code == 200
    assert log.json()["total"] >= 1


def test_admin_cannot_demote_self(client: TestClient) -> None:
    admin = _make_user(client, "admin4@example.com", "admin4")
    resp = client.patch(
        f"{ADMIN_USERS}/{admin['user']['id']}/role",
        headers=_auth(admin["tokens"]),
        json={"role": "user"},
    )
    assert resp.status_code == 400


def test_ban_and_unban_user(client: TestClient, db_session: Session) -> None:
    admin = _make_user(client, "admin5@example.com", "admin5")
    victim = _make_user(client, "victim@example.com", "victim")
    vid = victim["user"]["id"]

    ban = client.post(
        f"{ADMIN_USERS}/{vid}/ban",
        headers=_auth(admin["tokens"]),
        json={"reason": "spamming", "duration_hours": 24},
    )
    assert ban.status_code == 200, ban.text
    assert ban.json()["action"] == "ban"

    u = db_session.get(User, __import__("uuid").UUID(vid))
    db_session.refresh(u)
    assert u.is_active is False

    # A banned user's existing token is rejected (403 account disabled).
    assert client.get("/api/v1/auth/me", headers=_auth(victim["tokens"])).status_code == 403

    unban = client.post(f"{ADMIN_USERS}/{vid}/unban", headers=_auth(admin["tokens"]))
    assert unban.status_code == 200
    db_session.refresh(u)
    assert u.is_active is True


def test_ban_requires_admin(client: TestClient) -> None:
    _make_user(client, "admin6@example.com", "admin6")
    member = _make_user(client, "member6@example.com", "member6")
    resp = client.post(
        f"{ADMIN_USERS}/{member['user']['id']}/ban",
        headers=_auth(member["tokens"]),
        json={"reason": "nope"},
    )
    assert resp.status_code == 403


def test_moderator_may_list_but_not_ban(client: TestClient, db_session: Session) -> None:
    _make_user(client, "admin7@example.com", "admin7")
    mod = _make_user(client, "mod7@example.com", "mod7")
    u = db_session.query(User).filter_by(email="mod7@example.com").one()
    u.role = UserRole.MODERATOR
    db_session.add(u)
    db_session.commit()
    login = client.post(LOGIN, json={"email": "mod7@example.com", "password": "RallyPass123"})
    headers = _auth(login.json()["tokens"])

    assert client.get(ADMIN_USERS, headers=headers).status_code == 200
    victim = _make_user(client, "victim7@example.com", "victim7")
    resp = client.post(
        f"{ADMIN_USERS}/{victim['user']['id']}/ban", headers=headers, json={"reason": "x"}
    )
    assert resp.status_code == 403
