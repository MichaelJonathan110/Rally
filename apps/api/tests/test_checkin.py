"""Check-in tests: confirmed-only, time-window, idempotency, attendance + reputation."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError
from app.models.activity import ActivityParticipant
from app.models.enums import ParticipantStatus
from app.services.checkin_service import (
    REP_ATTENDED_DELTA,
    REP_NO_SHOW_DELTA,
    CheckInService,
)

ACTIVITIES = "/api/v1/activities"
REGISTER = "/api/v1/auth/register"
ME = "/api/v1/auth/me"


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
        "title": "Checkin Match",
        "category": "sports",
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T12:00:00Z",
        "max_participants": 4,
    }
    payload.update(overrides)
    resp = client.post(ACTIVITIES, json=payload, headers=_auth(host))
    assert resp.status_code == 201, resp.text
    return resp.json()


def _open_window() -> dict[str, str]:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    return {
        "starts_at": (now - timedelta(minutes=1)).isoformat(),
        "ends_at": (now + timedelta(hours=2)).isoformat(),
    }


def _reputation(client: TestClient, user: dict) -> int:
    resp = client.get(ME, headers=_auth(user))
    assert resp.status_code == 200, resp.text
    return resp.json()["profile"]["reputation_score"]


def _participant_status(db: Session, activity_id: str, user_id: str) -> ParticipantStatus:
    row = db.scalar(
        select(ActivityParticipant).where(
            ActivityParticipant.activity_id == uuid.UUID(activity_id),
            ActivityParticipant.user_id == uuid.UUID(user_id),
        )
    )
    assert row is not None
    return row.status


def test_host_can_check_in_within_window(client: TestClient) -> None:
    host = _register(client, "ch1@example.com", "checkhost1")
    activity = _make_activity(client, host, **_open_window())
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["activity_id"] == activity["id"]


def test_checkin_before_window_rejected(client: TestClient) -> None:
    host = _register(client, "ch2@example.com", "checkhost2")
    activity = _make_activity(client, host)  # starts 2030 -> window not open
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    assert resp.status_code == 409, resp.text


def test_non_participant_cannot_check_in(client: TestClient) -> None:
    host = _register(client, "ch3@example.com", "checkhost3")
    stranger = _register(client, "ch4@example.com", "checkstranger")
    activity = _make_activity(client, host, **_open_window())
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(stranger),
    )
    assert resp.status_code == 403, resp.text


def test_checkin_is_idempotent(client: TestClient) -> None:
    host = _register(client, "ch5@example.com", "checkhost5")
    activity = _make_activity(client, host, **_open_window())
    first = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    second = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_host_lists_checkins_and_others_forbidden(client: TestClient) -> None:
    host = _register(client, "ch6@example.com", "checkhost6")
    stranger = _register(client, "ch7@example.com", "checkstranger7")
    activity = _make_activity(client, host, **_open_window())
    client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    ok = client.get(
        f"{ACTIVITIES}/{activity['id']}/checkins", headers=_auth(host)
    )
    assert ok.status_code == 200, ok.text
    assert len(ok.json()) == 1

    forbidden = client.get(
        f"{ACTIVITIES}/{activity['id']}/checkins", headers=_auth(stranger)
    )
    assert forbidden.status_code == 403, forbidden.text


def test_checkin_unknown_activity_404(client: TestClient) -> None:
    host = _register(client, "ch8@example.com", "checkhost8")
    resp = client.post(
        f"{ACTIVITIES}/{uuid.uuid4()}/checkin",
        json={"method": "manual"},
        headers=_auth(host),
    )
    assert resp.status_code == 404, resp.text


# -- attendance + reputation -------------------------------------------------


def test_confirmed_checkin_sets_attended_and_credits_reputation(
    client: TestClient, db_session: Session
) -> None:
    host = _register(client, "ch10@example.com", "checkhost10")
    player = _register(client, "ch11@example.com", "checkplayer11")
    activity = _make_activity(client, host, **_open_window())
    join = client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))
    assert join.status_code in (200, 201), join.text
    assert join.json()["status"] == ParticipantStatus.CONFIRMED.value

    before = _reputation(client, player)
    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(player),
    )
    assert resp.status_code == 201, resp.text

    assert (
        _participant_status(db_session, activity["id"], player["user"]["id"])
        == ParticipantStatus.ATTENDED
    )
    assert _reputation(client, player) == before + REP_ATTENDED_DELTA


def test_waitlisted_cannot_check_in(client: TestClient) -> None:
    host = _register(client, "ch12@example.com", "checkhost12")
    player = _register(client, "ch13@example.com", "checkplayer13")
    # Host occupies the single slot, so the joiner is waitlisted.
    activity = _make_activity(client, host, max_participants=1, **_open_window())
    join = client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))
    assert join.status_code in (200, 201), join.text
    assert join.json()["status"] == ParticipantStatus.WAITLISTED.value

    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(player),
    )
    assert resp.status_code == 403, resp.text


def test_cancelled_cannot_check_in(client: TestClient, db_session: Session) -> None:
    host = _register(client, "ch14@example.com", "checkhost14")
    player = _register(client, "ch15@example.com", "checkplayer15")
    activity = _make_activity(client, host, **_open_window())
    join = client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))
    assert join.status_code in (200, 201), join.text

    row = db_session.scalar(
        select(ActivityParticipant).where(
            ActivityParticipant.activity_id == uuid.UUID(activity["id"]),
            ActivityParticipant.user_id == uuid.UUID(player["user"]["id"]),
        )
    )
    assert row is not None
    row.status = ParticipantStatus.CANCELLED
    db_session.commit()

    resp = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(player),
    )
    assert resp.status_code == 403, resp.text


def test_duplicate_checkin_does_not_double_reputation(client: TestClient) -> None:
    host = _register(client, "ch16@example.com", "checkhost16")
    player = _register(client, "ch17@example.com", "checkplayer17")
    activity = _make_activity(client, host, **_open_window())
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))

    before = _reputation(client, player)
    first = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(player),
    )
    second = client.post(
        f"{ACTIVITIES}/{activity['id']}/checkin",
        json={"method": "manual"},
        headers=_auth(player),
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert _reputation(client, player) == before + REP_ATTENDED_DELTA


def test_host_can_mark_no_show(client: TestClient, db_session: Session) -> None:
    host = _register(client, "ch18@example.com", "checkhost18")
    player = _register(client, "ch19@example.com", "checkplayer19")
    activity = _make_activity(client, host, **_open_window())
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))

    before = _reputation(client, player)
    participant = CheckInService(db_session).mark_no_show(
        uuid.UUID(activity["id"]),
        uuid.UUID(player["user"]["id"]),
        uuid.UUID(host["user"]["id"]),
    )
    assert participant.status == ParticipantStatus.NO_SHOW
    assert (
        _participant_status(db_session, activity["id"], player["user"]["id"])
        == ParticipantStatus.NO_SHOW
    )
    assert _reputation(client, player) == before + REP_NO_SHOW_DELTA


def test_mark_no_show_is_idempotent(client: TestClient, db_session: Session) -> None:
    host = _register(client, "ch20@example.com", "checkhost20")
    player = _register(client, "ch21@example.com", "checkplayer21")
    activity = _make_activity(client, host, **_open_window())
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))

    before = _reputation(client, player)
    service = CheckInService(db_session)
    aid, uid, actor = (
        uuid.UUID(activity["id"]),
        uuid.UUID(player["user"]["id"]),
        uuid.UUID(host["user"]["id"]),
    )
    service.mark_no_show(aid, uid, actor)
    service.mark_no_show(aid, uid, actor)
    assert _reputation(client, player) == before + REP_NO_SHOW_DELTA


def test_non_host_cannot_mark_no_show(client: TestClient, db_session: Session) -> None:
    host = _register(client, "ch22@example.com", "checkhost22")
    player = _register(client, "ch23@example.com", "checkplayer23")
    stranger = _register(client, "ch24@example.com", "checkstranger24")
    activity = _make_activity(client, host, **_open_window())
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(player))

    with pytest.raises(PermissionDeniedError):
        CheckInService(db_session).mark_no_show(
            uuid.UUID(activity["id"]),
            uuid.UUID(player["user"]["id"]),
            uuid.UUID(stranger["user"]["id"]),
        )
