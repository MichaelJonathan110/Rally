"""Notification tests: created on join, booking confirm, payment, cancellation;
inbox listing, unread count, mark-read (own only)."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.notification_service import NotificationService

ACTIVITIES = "/api/v1/activities"
BOOKINGS = "/api/v1/bookings"
VENUES = "/api/v1/venues"
NOTIFICATIONS = "/api/v1/notifications"
REGISTER = "/api/v1/auth/register"


def _register(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(body: dict) -> dict[str, str]:
    token = body.get("tokens", body)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_activity(client: TestClient, host: dict, **overrides) -> dict:
    payload = {
        "title": "Notify Activity",
        "category": "sports",
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T12:00:00Z",
        "max_participants": 6,
    }
    payload.update(overrides)
    resp = client.post(ACTIVITIES, json=payload, headers=_auth(host))
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_court(client: TestClient, owner: dict, price: int = 2000) -> str:
    venue = client.post(
        VENUES,
        json={
            "name": "Notify Venue",
            "city": "Berlin",
            "courts": [
                {
                    "name": "Court N",
                    "surface": "clay",
                    "capacity": 4,
                    "hourly_price_cents": price,
                }
            ],
        },
        headers=_auth(owner),
    ).json()
    return client.get(f"{VENUES}/{venue['id']}/courts").json()[0]["id"]


def test_notification_created_on_join(client: TestClient) -> None:
    host = _register(client, "n1@example.com", "nothost1")
    joiner = _register(client, "n2@example.com", "nojoin2")
    activity = _make_activity(client, host)
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner)
    )
    assert resp.status_code == 200, resp.text

    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    assert inbox["total"] >= 1
    assert any("joined" in n["title"].lower() for n in inbox["items"])
    assert inbox["unread_count"] >= 1


def test_notification_created_on_booking_confirm_and_payment(
    client: TestClient,
) -> None:
    owner = _register(client, "n3@example.com", "notowner3")
    court_id = _make_court(client, owner)
    booking = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T11:00:00Z",
            "total_price_cents": 1000,
            "currency": "EUR",
        },
        headers=_auth(owner),
    ).json()
    client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "notify-pay-1"},
        headers=_auth(owner),
    )
    client.post(
        f"{BOOKINGS}/{booking['id']}/confirm", headers=_auth(owner)
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(owner)).json()
    titles = [n["title"].lower() for n in inbox["items"]]
    assert any("confirm" in t for t in titles), titles


def test_notification_created_on_activity_cancel(client: TestClient) -> None:
    host = _register(client, "n4@example.com", "nothost4")
    member = _register(client, "n5@example.com", "nomember5")
    activity = _make_activity(client, host)
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(member))
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/cancel", headers=_auth(host)
    )
    assert resp.status_code == 200, resp.text
    inbox = client.get(NOTIFICATIONS, headers=_auth(member)).json()
    assert any("cancel" in n["title"].lower() for n in inbox["items"])


def test_mark_read_and_unread_only_filter(client: TestClient) -> None:
    host = _register(client, "n6@example.com", "nothost6")
    joiner = _register(client, "n7@example.com", "nojoin7")
    activity = _make_activity(client, host)
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner))

    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    first = inbox["items"][0]
    read = client.post(
        f"{NOTIFICATIONS}/{first['id']}/read", headers=_auth(host)
    )
    assert read.status_code == 200, read.text
    assert read.json()["is_read"] is True

    unread = client.get(
        f"{NOTIFICATIONS}?unread_only=true", headers=_auth(host)
    ).json()
    assert all(not n["is_read"] for n in unread["items"])


def test_cannot_read_another_users_notification(client: TestClient) -> None:
    host = _register(client, "n8@example.com", "nothost8")
    joiner = _register(client, "n9@example.com", "nojoin9")
    stranger = _register(client, "n10@example.com", "nostranger10")
    activity = _make_activity(client, host)
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner))
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    first = inbox["items"][0]
    resp = client.post(
        f"{NOTIFICATIONS}/{first['id']}/read", headers=_auth(stranger)
    )
    assert resp.status_code == 403, resp.text


def test_notifications_require_auth(client: TestClient) -> None:
    assert client.get(NOTIFICATIONS).status_code == 401


def test_mark_read_unknown_notification_404(client: TestClient) -> None:
    user = _register(client, "n11@example.com", "nouser11")
    resp = client.post(
        f"{NOTIFICATIONS}/{uuid.uuid4()}/read", headers=_auth(user)
    )
    assert resp.status_code == 404, resp.text


# --- typed event helpers -------------------------------------------------

def _register_ids(client: TestClient, suffix: str) -> tuple[dict, dict]:
    host = _register(client, f"h{suffix}@example.com", f"host{suffix}")
    other = _register(client, f"o{suffix}@example.com", f"other{suffix}")
    return host, other


def test_notify_activity_joined_persists_and_is_idempotent(
    client: TestClient, db_session: Session
) -> None:
    host, joiner = _register_ids(client, "h1")
    activity_id = uuid.uuid4()
    service = NotificationService(db_session)
    service.notify_activity_joined(
        host_id=uuid.UUID(host["user"]["id"]),
        joiner_id=uuid.UUID(joiner["user"]["id"]),
        activity_id=activity_id,
        activity_title="Rally Doubles",
        sport_slug="tennis",
    )
    # same event key -> no duplicate
    service.notify_activity_joined(
        host_id=uuid.UUID(host["user"]["id"]),
        joiner_id=uuid.UUID(joiner["user"]["id"]),
        activity_id=activity_id,
        activity_title="Rally Doubles",
        sport_slug="tennis",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    assert inbox["total"] == 1, inbox
    item = inbox["items"][0]
    assert "joined" in item["title"].lower()
    assert item["data"]["activity_id"] == str(activity_id)
    assert item["data"]["sport_slug"] == "tennis"


def test_notify_waitlist_promoted(client: TestClient, db_session: Session) -> None:
    host, joiner = _register_ids(client, "h2")
    activity_id = uuid.uuid4()
    NotificationService(db_session).notify_waitlist_promoted(
        user_id=uuid.UUID(joiner["user"]["id"]),
        activity_id=activity_id,
        activity_title="Rally Doubles",
        sport_slug="padel",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(joiner)).json()
    assert inbox["total"] == 1, inbox
    item = inbox["items"][0]
    assert "waitlist" in item["title"].lower()
    assert item["data"]["sport_slug"] == "padel"
    assert item["data"]["promoted"] is True


def test_notify_booking_confirmed(client: TestClient, db_session: Session) -> None:
    host, _ = _register_ids(client, "h3")
    booking_id = uuid.uuid4()
    NotificationService(db_session).notify_booking_confirmed(
        user_id=uuid.UUID(host["user"]["id"]),
        booking_id=booking_id,
        sport_slug="squash",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    item = inbox["items"][0]
    assert item["data"]["booking_id"] == str(booking_id)
    assert item["data"]["sport_slug"] == "squash"
    assert "confirm" in item["title"].lower()


def test_notify_payment_succeeded(client: TestClient, db_session: Session) -> None:
    host, _ = _register_ids(client, "h4")
    booking_id, payment_id = uuid.uuid4(), uuid.uuid4()
    NotificationService(db_session).notify_payment_succeeded(
        user_id=uuid.UUID(host["user"]["id"]),
        booking_id=booking_id,
        payment_id=payment_id,
        amount_cents=1500,
        currency="EUR",
        sport_slug="tennis",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    item = inbox["items"][0]
    assert item["data"]["payment_id"] == str(payment_id)
    assert item["data"]["amount_cents"] == 1500
    assert item["data"]["sport_slug"] == "tennis"
    assert "payment" in item["title"].lower()


def test_notify_checkin_recorded(client: TestClient, db_session: Session) -> None:
    host, _ = _register_ids(client, "h5")
    activity_id = uuid.uuid4()
    NotificationService(db_session).notify_checkin_recorded(
        user_id=uuid.UUID(host["user"]["id"]),
        activity_id=activity_id,
        sport_slug="basketball",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    item = inbox["items"][0]
    assert item["data"]["activity_id"] == str(activity_id)
    assert item["data"]["sport_slug"] == "basketball"
    assert "check-in" in item["title"].lower()


def test_notify_mmr_changed(client: TestClient, db_session: Session) -> None:
    host, _ = _register_ids(client, "h6")
    NotificationService(db_session).notify_mmr_changed(
        user_id=uuid.UUID(host["user"]["id"]),
        delta=12.5,
        sport_slug="tennis",
        category="racket",
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    item = inbox["items"][0]
    assert item["data"]["sport_slug"] == "tennis"
    assert item["data"]["delta"] == 12.5
    assert "mmr" in item["title"].lower()


def test_unread_query_alias_filters(client: TestClient, db_session: Session) -> None:
    host, _ = _register_ids(client, "h7")
    service = NotificationService(db_session)
    uid = uuid.UUID(host["user"]["id"])
    service.notify_checkin_recorded(
        user_id=uid, activity_id=uuid.uuid4(), sport_slug="tennis"
    )
    service.notify_booking_confirmed(
        user_id=uid, booking_id=uuid.uuid4(), sport_slug="tennis"
    )
    inbox = client.get(NOTIFICATIONS, headers=_auth(host)).json()
    first = inbox["items"][0]
    client.post(f"{NOTIFICATIONS}/{first['id']}/read", headers=_auth(host))

    unread = client.get(f"{NOTIFICATIONS}?unread=true", headers=_auth(host)).json()
    assert unread["total"] == 1
    assert all(not n["is_read"] for n in unread["items"])

    unread_legacy = client.get(
        f"{NOTIFICATIONS}?unread_only=true", headers=_auth(host)
    ).json()
    assert unread_legacy["total"] == 1
