"""Public user profile sports endpoint tests.

The profile must expose a user's SPORT-SPECIFIC data (skill, matches, MMR) read
from the real ``mmr_ratings`` store - never a fake/invented number.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rating import MmrRating

REGISTER = "/api/v1/auth/register"


def _register(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _add_rating(
    db: Session,
    user_id: str,
    sport_slug: str,
    rating: float,
    games: int,
) -> None:
    db.add(
        MmrRating(
            user_id=uuid.UUID(user_id),
            category="racket",
            sport_slug=sport_slug,
            rating=rating,
            games_played=games,
        )
    )
    db.commit()


def test_profile_sports_lists_user_ratings(client: TestClient, db_session: Session) -> None:
    body = _register(client, "sports-a@example.com", "sports_a")
    user_id = body["user"]["id"]
    _add_rating(db_session, user_id, "padel", 1310.5, 7)
    _add_rating(db_session, user_id, "tennis", 1225.0, 3)

    resp = client.get(f"/api/v1/users/{user_id}/sports")
    assert resp.status_code == 200, resp.text
    rows = {r["sport_slug"]: r for r in resp.json()}

    assert set(rows) == {"padel", "tennis"}
    assert rows["padel"]["label"] == "Padel"
    assert rows["padel"]["matches_played"] == 7
    assert rows["padel"]["rating"] == 1310.5
    assert rows["padel"]["ranked"] is True
    assert rows["tennis"]["matches_played"] == 3
    assert rows["tennis"]["ranked"] is True


def test_profile_sports_unranked_when_no_matches(
    client: TestClient, db_session: Session
) -> None:
    body = _register(client, "sports-b@example.com", "sports_b")
    user_id = body["user"]["id"]
    # Rating row exists but no verified matches yet -> UNRANKED, no fake number.
    _add_rating(db_session, user_id, "squash", 1200.0, 0)

    resp = client.get(f"/api/v1/users/{user_id}/sports")
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["sport_slug"] == "squash"
    assert rows[0]["ranked"] is False
    assert rows[0]["rating"] is None
    assert rows[0]["matches_played"] == 0


def test_profile_sports_scoped_to_that_user(client: TestClient, db_session: Session) -> None:
    a = _register(client, "sports-c@example.com", "sports_c")["user"]["id"]
    b = _register(client, "sports-d@example.com", "sports_d")["user"]["id"]
    _add_rating(db_session, a, "badminton", 1400.0, 5)
    _add_rating(db_session, b, "pickleball", 1150.0, 4)

    resp = client.get(f"/api/v1/users/{a}/sports")
    assert resp.status_code == 200, resp.text
    slugs = {r["sport_slug"] for r in resp.json()}
    assert slugs == {"badminton"}


def test_profile_sports_unknown_user_is_404(client: TestClient) -> None:
    resp = client.get(f"/api/v1/users/{uuid.uuid4()}/sports")
    assert resp.status_code == 404
