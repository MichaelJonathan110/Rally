"""Booking API tests: create (price + splits), list, cancel, RBAC, 404s."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

BOOKINGS = "/api/v1/bookings"
VENUES = "/api/v1/venues"
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


def _make_court(client: TestClient, owner_tokens: dict, price: int = 2000) -> str:
    venue = client.post(
        VENUES,
        json={
            "name": "Booking Venue",
            "city": "Berlin",
            "courts": [
                {
                    "name": "Court A",
                    "surface": "clay",
                    "capacity": 4,
                    "hourly_price_cents": price,
                }
            ],
        },
        headers=_auth(owner_tokens),
    ).json()
    courts = client.get(f"{VENUES}/{venue['id']}/courts").json()
    return courts[0]["id"]


def test_create_booking_derives_price_from_court(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=2000)
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T12:00:00Z",
            "currency": "EUR",
        },
        headers=_auth(owner),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # 2 hours * 2000 cents
    assert body["total_price_cents"] == 4000
    assert body["status"] == "pending"
    assert len(body["payments"]) == 1
    assert body["payments"][0]["provider"] == "mock"
    assert len(body["splits"]) == 1
    assert body["splits"][0]["share_cents"] == 4000


def test_create_booking_requires_auth(client: TestClient) -> None:
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": str(uuid.uuid4()),
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T12:00:00Z",
        },
    )
    assert resp.status_code == 401


def test_create_booking_splits_between_users(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    friend = _register(client, "friend@example.com", "friend")
    friend_id = client.get("/api/v1/auth/me", headers=_auth(friend)).json()["id"]
    court_id = _make_court(client, owner, price=3000)
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T11:00:00Z",
            "currency": "EUR",
            "split_between_user_ids": [friend_id],
        },
        headers=_auth(owner),
    )
    assert resp.status_code == 201, resp.text
    splits = resp.json()["splits"]
    assert len(splits) == 2
    assert sum(s["share_cents"] for s in splits) == 3000


def test_create_booking_validation_error(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner)
    bad = {
        "venue_court_id": court_id,
        "starts_at": "2030-01-01T12:00:00Z",
        "ends_at": "2030-01-01T10:00:00Z",  # ends before starts
    }
    assert client.post(BOOKINGS, json=bad, headers=_auth(owner)).status_code == 422


def test_create_booking_unknown_court_400(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": str(uuid.uuid4()),
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T11:00:00Z",
        },
        headers=_auth(owner),
    )
    assert resp.status_code == 400


def test_create_booking_idempotent_replay(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    payload = {
        "venue_court_id": court_id,
        "starts_at": "2030-02-01T10:00:00Z",
        "ends_at": "2030-02-01T11:00:00Z",
        "idempotency_key": "unique-key-12345678",
    }
    first = client.post(BOOKINGS, json=payload, headers=_auth(owner)).json()
    second = client.post(BOOKINGS, json=payload, headers=_auth(owner)).json()
    assert first["id"] == second["id"]


def test_create_booking_overlapping_conflict(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    payload = {
        "venue_court_id": court_id,
        "starts_at": "2030-03-01T10:00:00Z",
        "ends_at": "2030-03-01T12:00:00Z",
    }
    assert client.post(BOOKINGS, json=payload, headers=_auth(owner)).status_code == 201
    overlap = {
        "venue_court_id": court_id,
        "starts_at": "2030-03-01T11:00:00Z",
        "ends_at": "2030-03-01T13:00:00Z",
    }
    assert client.post(BOOKINGS, json=overlap, headers=_auth(owner)).status_code == 409


def test_list_bookings_only_mine(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    other = _register(client, "other@example.com", "other")
    court_id = _make_court(client, owner, price=1000)
    client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-04-01T10:00:00Z",
            "ends_at": "2030-04-01T11:00:00Z",
        },
        headers=_auth(owner),
    )
    resp = client.get(BOOKINGS, headers=_auth(other))
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 0


def test_list_bookings_requires_auth(client: TestClient) -> None:
    assert client.get(BOOKINGS).status_code == 401


def test_get_booking_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    created = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-05-01T10:00:00Z",
            "ends_at": "2030-05-01T11:00:00Z",
        },
        headers=_auth(owner),
    ).json()
    resp = client.get(f"{BOOKINGS}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_booking_not_found_404(client: TestClient) -> None:
    assert client.get(f"{BOOKINGS}/{uuid.uuid4()}").status_code == 404


def test_cancel_booking_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    created = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-06-01T10:00:00Z",
            "ends_at": "2030-06-01T11:00:00Z",
        },
        headers=_auth(owner),
    ).json()
    resp = client.post(f"{BOOKINGS}/{created['id']}/cancel", headers=_auth(owner))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled"


def test_cancel_booking_non_booker_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    other = _register(client, "other@example.com", "other")
    court_id = _make_court(client, owner, price=1000)
    created = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-07-01T10:00:00Z",
            "ends_at": "2030-07-01T11:00:00Z",
        },
        headers=_auth(owner),
    ).json()
    resp = client.post(f"{BOOKINGS}/{created['id']}/cancel", headers=_auth(other))
    assert resp.status_code == 403


def test_cancel_booking_not_found_404(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.post(f"{BOOKINGS}/{uuid.uuid4()}/cancel", headers=_auth(owner))
    assert resp.status_code == 404


def _create_booking(client: TestClient, tokens: dict, court_id: str, hour: int) -> dict:
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": f"2030-09-01T{hour:02d}:00:00Z",
            "ends_at": f"2030-09-01T{hour + 1:02d}:00:00Z",
        },
        headers=_auth(tokens),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_complete_confirmed_booking_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    booking = _create_booking(client, owner, court_id, 10)
    assert booking["status"] == "pending"

    confirmed = client.post(
        f"{BOOKINGS}/{booking['id']}/confirm", headers=_auth(owner)
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"

    resp = client.post(f"{BOOKINGS}/{booking['id']}/complete", headers=_auth(owner))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"


def test_complete_pending_booking_rejected_409(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    booking = _create_booking(client, owner, court_id, 11)
    assert booking["status"] == "pending"

    resp = client.post(f"{BOOKINGS}/{booking['id']}/complete", headers=_auth(owner))
    assert resp.status_code == 409, resp.text
    # The booking is untouched by the rejected transition.
    after = client.get(f"{BOOKINGS}/{booking['id']}").json()
    assert after["status"] == "pending"


def test_complete_completed_booking_again_rejected_409(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    court_id = _make_court(client, owner, price=1000)
    booking = _create_booking(client, owner, court_id, 12)
    client.post(f"{BOOKINGS}/{booking['id']}/confirm", headers=_auth(owner))
    first = client.post(f"{BOOKINGS}/{booking['id']}/complete", headers=_auth(owner))
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "completed"

    again = client.post(f"{BOOKINGS}/{booking['id']}/complete", headers=_auth(owner))
    assert again.status_code == 409, again.text
    # A completed booking is terminal: it cannot be cancelled either.
    cancel = client.post(f"{BOOKINGS}/{booking['id']}/cancel", headers=_auth(owner))
    assert cancel.status_code == 409, cancel.text
    assert client.get(f"{BOOKINGS}/{booking['id']}").json()["status"] == "completed"


def test_complete_booking_non_owner_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    other = _register(client, "other@example.com", "other")
    court_id = _make_court(client, owner, price=1000)
    booking = _create_booking(client, owner, court_id, 13)
    client.post(f"{BOOKINGS}/{booking['id']}/confirm", headers=_auth(owner))

    resp = client.post(f"{BOOKINGS}/{booking['id']}/complete", headers=_auth(other))
    assert resp.status_code == 403, resp.text
    assert client.get(f"{BOOKINGS}/{booking['id']}").json()["status"] == "confirmed"
