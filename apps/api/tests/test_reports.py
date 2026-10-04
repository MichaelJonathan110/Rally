"""Reports, venue reviews and achievements: RBAC + happy paths."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.social import Achievement, UserAchievement
from app.models.user import User

REGISTER = "/api/v1/auth/register"
REPORTS = "/api/v1/reports"
ADMIN_REPORTS = "/api/v1/admin/reports"
VENUES = "/api/v1/venues"


def _make_user(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER, json={"email": email, "username": username, "password": "RallyPass123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# --- reports ---------------------------------------------------------------
def test_report_requires_auth(client: TestClient) -> None:
    resp = client.post(
        REPORTS,
        json={"target_type": "user", "target_id": str(uuid.uuid4()), "reason": "spam"},
    )
    assert resp.status_code == 401


def test_any_user_can_file_report(client: TestClient) -> None:
    user = _make_user(client, "reporter@example.com", "reporter")
    resp = client.post(
        REPORTS,
        headers=_auth(user["tokens"]),
        json={
            "target_type": "user",
            "target_id": str(uuid.uuid4()),
            "reason": "harassment",
            "details": "abusive messages in chat",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "open"
    assert body["reporter_id"] == user["user"]["id"]


def test_report_rejects_markup(client: TestClient) -> None:
    user = _make_user(client, "reporter2@example.com", "reporter2")
    resp = client.post(
        REPORTS,
        headers=_auth(user["tokens"]),
        json={
            "target_type": "user",
            "target_id": str(uuid.uuid4()),
            "reason": "<script>alert(1)</script>",
        },
    )
    assert resp.status_code == 422


def test_moderator_can_list_reports(client: TestClient, db_session: Session) -> None:
    from app.models.enums import UserRole

    admin = _make_user(client, "admin@example.com", "admin")
    _make_user(client, "rep@example.com", "rep")
    mod = _make_user(client, "mod@example.com", "mod")
    u = db_session.query(User).filter_by(email="mod@example.com").one()
    u.role = UserRole.MODERATOR
    db_session.add(u)
    db_session.commit()

    client.post(
        REPORTS,
        headers=_auth(mod["tokens"]),
        json={"target_type": "user", "target_id": str(uuid.uuid4()), "reason": "test"},
    )
    resp = client.get(ADMIN_REPORTS, headers=_auth(admin["tokens"]))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_resolve_report_admin_only(client: TestClient) -> None:
    admin = _make_user(client, "admin2@example.com", "admin2")
    member = _make_user(client, "member@example.com", "member")

    created = client.post(
        REPORTS,
        headers=_auth(member["tokens"]),
        json={"target_type": "user", "target_id": str(uuid.uuid4()), "reason": "abuse"},
    ).json()

    forbidden = client.post(
        f"{ADMIN_REPORTS}/{created['id']}/resolve",
        headers=_auth(member["tokens"]),
        json={"status": "resolved", "note": "done"},
    )
    assert forbidden.status_code == 403

    ok = client.post(
        f"{ADMIN_REPORTS}/{created['id']}/resolve",
        headers=_auth(admin["tokens"]),
        json={"status": "resolved", "note": "handled", "action": "warn"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "resolved"
    assert ok.json()["resolved_by_id"] == admin["user"]["id"]


def test_cannot_resolve_twice(client: TestClient) -> None:
    admin = _make_user(client, "admin3@example.com", "admin3")
    created = client.post(
        REPORTS,
        headers=_auth(admin["tokens"]),
        json={"target_type": "user", "target_id": str(uuid.uuid4()), "reason": "abuse"},
    ).json()
    first = client.post(
        f"{ADMIN_REPORTS}/{created['id']}/resolve",
        headers=_auth(admin["tokens"]),
        json={"status": "dismissed"},
    )
    assert first.status_code == 200
    second = client.post(
        f"{ADMIN_REPORTS}/{created['id']}/resolve",
        headers=_auth(admin["tokens"]),
        json={"status": "resolved"},
    )
    assert second.status_code == 409


# --- reviews ---------------------------------------------------------------
def _create_venue(client: TestClient, headers: dict) -> dict:
    payload = {
        "name": "Test Arena",
        "address_line": "1 Main St",
        "city": "Berlin",
        "country": "DE",
        "courts": [{"name": "C1", "surface": "hard", "capacity": 4, "hourly_price_cents": 1000}],
    }
    resp = client.post(VENUES, json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_list_reviews(client: TestClient) -> None:
    owner = _make_user(client, "vowner@example.com", "vowner")
    venue = _create_venue(client, _auth(owner["tokens"]))
    reviewer = _make_user(client, "rev@example.com", "rev")

    created = client.post(
        f"{VENUES}/{venue['id']}/reviews",
        headers=_auth(reviewer["tokens"]),
        json={"rating": 5, "body": "Great courts"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["rating"] == 5

    summary = client.get(f"{VENUES}/{venue['id']}/reviews")
    assert summary.status_code == 200
    body = summary.json()
    assert body["review_count"] == 1
    assert body["average_rating"] == 5.0


def test_duplicate_review_rejected(client: TestClient) -> None:
    owner = _make_user(client, "vowner2@example.com", "vowner2")
    venue = _create_venue(client, _auth(owner["tokens"]))
    reviewer = _make_user(client, "rev2@example.com", "rev2")
    h = _auth(reviewer["tokens"])
    first = client.post(f"{VENUES}/{venue['id']}/reviews", headers=h, json={"rating": 4})
    assert first.status_code == 201
    dup = client.post(f"{VENUES}/{venue['id']}/reviews", headers=h, json={"rating": 3})
    assert dup.status_code == 409


def test_review_rating_bounds(client: TestClient) -> None:
    owner = _make_user(client, "vowner3@example.com", "vowner3")
    venue = _create_venue(client, _auth(owner["tokens"]))
    reviewer = _make_user(client, "rev3@example.com", "rev3")
    bad = client.post(
        f"{VENUES}/{venue['id']}/reviews", headers=_auth(reviewer["tokens"]), json={"rating": 9}
    )
    assert bad.status_code == 422


def test_review_unknown_venue_404(client: TestClient) -> None:
    user = _make_user(client, "rev4@example.com", "rev4")
    resp = client.post(
        f"{VENUES}/{uuid.uuid4()}/reviews", headers=_auth(user["tokens"]), json={"rating": 4}
    )
    assert resp.status_code == 404


# --- achievements ----------------------------------------------------------
def test_achievements_empty_then_populated(client: TestClient, db_session: Session) -> None:
    user = _make_user(client, "ach@example.com", "ach")
    uid = uuid.UUID(user["user"]["id"])

    assert client.get(f"/api/v1/users/{uid}/achievements").json() == []

    ach = Achievement(code="first_win", name="First Win", points=10)
    db_session.add(ach)
    db_session.commit()
    db_session.add(UserAchievement(user_id=uid, achievement_id=ach.id, earned_at=datetime.now(UTC)))
    db_session.commit()

    resp = client.get(f"/api/v1/users/{uid}/achievements")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["achievement"]["code"] == "first_win"


def test_achievements_unknown_user_404(client: TestClient) -> None:
    assert client.get(f"/api/v1/users/{uuid.uuid4()}/achievements").status_code == 404
