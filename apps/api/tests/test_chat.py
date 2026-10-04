"""Chat tests: lazy rooms, messages, membership and WebSocket broadcast."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

ACTIVITIES = "/api/v1/activities"
CHAT = "/api/v1/chat"
REGISTER = "/api/v1/auth/register"


def _register(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['tokens']['access_token']}"}


def _make_activity(client: TestClient, host: dict, **overrides) -> dict:
    payload = {
        "title": "Chat Activity",
        "category": "sports",
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T12:00:00Z",
        "max_participants": 6,
    }
    payload.update(overrides)
    resp = client.post(ACTIVITIES, json=payload, headers=_auth(host))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_empty_rooms_for_new_user(client: TestClient) -> None:
    user = _register(client, "c1@example.com", "chatuser1")
    resp = client.get(f"{CHAT}/rooms", headers=_auth(user))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_room_appears_after_joining_activity(client: TestClient) -> None:
    host = _register(client, "c2@example.com", "chathost2")
    joiner = _register(client, "c3@example.com", "chatjoin3")
    activity = _make_activity(client, host)
    assert client.post(
        f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner)
    ).status_code == 200

    rooms = client.get(f"{CHAT}/rooms", headers=_auth(joiner)).json()
    assert rooms["total"] >= 1
    room = rooms["items"][0]
    assert room["activity_id"] == activity["id"]
    assert room["type"] == "activity"


def test_send_and_list_messages(client: TestClient) -> None:
    host = _register(client, "c4@example.com", "chathost4")
    joiner = _register(client, "c5@example.com", "chatjoin5")
    activity = _make_activity(client, host)
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner))
    room_id = client.get(f"{CHAT}/rooms", headers=_auth(joiner)).json()["items"][0]["id"]

    sent = client.post(
        f"{CHAT}/rooms/{room_id}/messages",
        json={"body": "Hello room"},
        headers=_auth(joiner),
    )
    assert sent.status_code == 201, sent.text
    assert sent.json()["body"] == "Hello room"
    assert sent.json()["sender_name"] == "chatjoin5"

    listed = client.get(
        f"{CHAT}/rooms/{room_id}/messages", headers=_auth(host)
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["body"] == "Hello room"


def test_non_member_gets_403(client: TestClient) -> None:
    host = _register(client, "c6@example.com", "chathost6")
    stranger = _register(client, "c7@example.com", "chatstranger7")
    activity = _make_activity(client, host)
    room_id = client.get(f"{CHAT}/rooms", headers=_auth(host)).json()["items"][0]["id"]

    assert client.get(
        f"{CHAT}/rooms/{room_id}/messages", headers=_auth(stranger)
    ).status_code == 403
    assert client.post(
        f"{CHAT}/rooms/{room_id}/messages",
        json={"body": "sneaky"},
        headers=_auth(stranger),
    ).status_code == 403


def test_message_body_validation(client: TestClient) -> None:
    host = _register(client, "c8@example.com", "chathost8")
    activity = _make_activity(client, host)
    room_id = client.get(f"{CHAT}/rooms", headers=_auth(host)).json()["items"][0]["id"]
    assert client.post(
        f"{CHAT}/rooms/{room_id}/messages",
        json={"body": ""},
        headers=_auth(host),
    ).status_code == 422


def test_unknown_room_404(client: TestClient) -> None:
    host = _register(client, "c9@example.com", "chathost9")
    assert client.get(
        f"{CHAT}/rooms/{uuid.uuid4()}", headers=_auth(host)
    ).status_code == 404


def test_websocket_broadcasts_to_all_clients(client: TestClient) -> None:
    host = _register(client, "c10@example.com", "chathost10")
    joiner = _register(client, "c11@example.com", "chatjoin11")
    activity = _make_activity(client, host)
    client.post(f"{ACTIVITIES}/{activity['id']}/join", headers=_auth(joiner))
    room_id = client.get(f"{CHAT}/rooms", headers=_auth(host)).json()["items"][0]["id"]

    host_token = host["tokens"]["access_token"]
    joiner_token = joiner["tokens"]["access_token"]
    url = f"{CHAT}/ws?room_id={room_id}"

    with client.websocket_connect(f"{url}&token={host_token}") as ws1:
        with client.websocket_connect(f"{url}&token={joiner_token}") as ws2:
            ws1.send_json({"body": "live hello"})
            got1 = ws1.receive_json()
            got2 = ws2.receive_json()
            assert got1["type"] == "message"
            assert got1["message"]["body"] == "live hello"
            assert got2["message"]["body"] == "live hello"
            assert got2["message"]["sender_name"] == "chathost10"


def test_websocket_rejects_bad_token(client: TestClient) -> None:
    host = _register(client, "c12@example.com", "chathost12")
    activity = _make_activity(client, host)
    room_id = client.get(f"{CHAT}/rooms", headers=_auth(host)).json()["items"][0]["id"]
    import pytest

    with pytest.raises(Exception):
        with client.websocket_connect(f"{CHAT}/ws?room_id={room_id}&token=bogus"):
            pass
