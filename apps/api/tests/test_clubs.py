"""Club API tests: create, list/filter, join/leave, members, RBAC, 404s."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

CLUBS = "/api/v1/clubs"
REGISTER = "/api/v1/auth/register"


def _register(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["tokens"]


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _payload(**overrides) -> dict:
    base = {
        "name": "Berlin Runners",
        "slug": "berlin-runners",
        "description": "Weekly runs around the city",
        "category": "outdoor",
        "city": "Berlin",
        "is_public": True,
    }
    base.update(overrides)
    return base


def test_create_club_201_owner_is_member(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.post(CLUBS, json=_payload(), headers=_auth(owner))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Berlin Runners"
    assert body["slug"] == "berlin-runners"
    assert body["member_count"] == 1
    assert body["owner_id"]


def test_create_club_requires_auth(client: TestClient) -> None:
    assert client.post(CLUBS, json=_payload()).status_code == 401


def test_create_club_duplicate_slug_conflict(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    assert client.post(CLUBS, json=_payload(), headers=_auth(owner)).status_code == 201
    dup = client.post(CLUBS, json=_payload(), headers=_auth(owner))
    assert dup.status_code == 409


def test_create_club_validation_error(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    bad = _payload(slug="Bad Slug!")  # pattern violation
    assert client.post(CLUBS, json=bad, headers=_auth(owner)).status_code == 422


def test_list_clubs_paginated(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    for i in range(3):
        client.post(CLUBS, json=_payload(name=f"Club {i}", slug=f"club-{i}"), headers=_auth(owner))
    resp = client.get(CLUBS, params={"limit": 2})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_filter_clubs_by_category(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    client.post(CLUBS, json=_payload(name="Runners", slug="runners", category="outdoor"), headers=_auth(owner))
    client.post(CLUBS, json=_payload(name="Gamers", slug="gamers", category="games"), headers=_auth(owner))
    resp = client.get(CLUBS, params={"category": "games"})
    assert resp.status_code == 200, resp.text
    assert [c["name"] for c in resp.json()["items"]] == ["Gamers"]


def test_get_club_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    resp = client.get(f"{CLUBS}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_club_not_found_404(client: TestClient) -> None:
    assert client.get(f"{CLUBS}/{uuid.uuid4()}").status_code == 404


def test_join_club_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    resp = client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner))
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is True
    assert client.get(f"{CLUBS}/{created['id']}").json()["member_count"] == 2


def test_join_club_twice_conflict(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner))
    assert client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner)).status_code == 409


def test_join_private_club_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(
        CLUBS, json=_payload(is_public=False), headers=_auth(owner)
    ).json()
    assert client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner)).status_code == 403


def test_join_club_not_found_404(client: TestClient) -> None:
    joiner = _register(client, "joiner@example.com", "joiner")
    assert client.post(f"{CLUBS}/{uuid.uuid4()}/join", headers=_auth(joiner)).status_code == 404


def test_leave_club_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner))
    resp = client.post(f"{CLUBS}/{created['id']}/leave", headers=_auth(joiner))
    assert resp.status_code == 204
    assert client.get(f"{CLUBS}/{created['id']}").json()["member_count"] == 1


def test_leave_club_owner_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    resp = client.post(f"{CLUBS}/{created['id']}/leave", headers=_auth(owner))
    assert resp.status_code == 403


def test_list_members(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(CLUBS, json=_payload(), headers=_auth(owner)).json()
    client.post(f"{CLUBS}/{created['id']}/join", headers=_auth(joiner))
    resp = client.get(f"{CLUBS}/{created['id']}/members")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


def test_create_club_with_sport_ok(client: TestClient) -> None:
    """A club can be bound to a catalog sport; category is derived from it."""
    owner = _register(client, "owner@example.com", "owner")
    payload = {
        "name": "Berlin Padel",
        "slug": "berlin-padel",
        "description": "Padel club",
        "sport_slug": "padel",
        "city": "Berlin",
        "is_public": True,
    }
    resp = client.post(CLUBS, json=payload, headers=_auth(owner))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["sport_slug"] == "padel"
    assert body["sport_category"] == "racket"
    assert body["category"] == "sports"


def test_create_club_rejects_unknown_sport(client: TestClient) -> None:
    """RALLY is sports-only: an unknown sport slug is rejected with a 422."""
    owner = _register(client, "owner@example.com", "owner")
    bad = _payload(sport_slug="quidditch")
    resp = client.post(CLUBS, json=bad, headers=_auth(owner))
    assert resp.status_code == 422, resp.text


def test_list_clubs_filtered_by_sport(client: TestClient) -> None:
    """?sport=<slug> filters clubs by their bound sport (and validates it)."""
    owner = _register(client, "owner@example.com", "owner")
    padel = {
        "name": "Padel Crew",
        "slug": "padel-crew",
        "sport_slug": "padel",
        "city": "Berlin",
        "is_public": True,
    }
    tennis = {
        "name": "Tennis Crew",
        "slug": "tennis-crew",
        "sport_slug": "tennis",
        "city": "Berlin",
        "is_public": True,
    }
    assert client.post(CLUBS, json=padel, headers=_auth(owner)).status_code == 201
    assert client.post(CLUBS, json=tennis, headers=_auth(owner)).status_code == 201
    resp = client.get(CLUBS, params={"sport": "padel"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert [c["name"] for c in body["items"]] == ["Padel Crew"]
    # An unknown filter slug is a client error.
    assert client.get(CLUBS, params={"sport": "quidditch"}).status_code == 422
