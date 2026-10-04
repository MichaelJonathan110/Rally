"""Activity API tests: create, list, filter, join/leave, RBAC, 404s.

Runs against the real FastAPI app + in-memory SQLite (see ``conftest.py``).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

ACTIVITIES = "/api/v1/activities"
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


def _register_body(client: TestClient, email: str, username: str) -> dict:
    """Register and return the full body (``user`` + ``tokens``)."""
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _payload(**overrides) -> dict:
    base = {
        "title": "Sunday Football",
        "description": "Casual 5-a-side",
        "category": "sports",
        "skill_level": "intermediate",
        "visibility": "public",
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T12:00:00Z",
        "max_participants": 4,
        "currency": "EUR",
    }
    base.update(overrides)
    return base


def test_create_activity_returns_201_and_host_is_participant(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    resp = client.post(ACTIVITIES, json=_payload(), headers=_auth(host))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Sunday Football"
    assert body["category"] == "sports"
    assert body["participant_count"] == 1  # host auto-joined
    assert body["id"]


def test_create_activity_requires_auth(client: TestClient) -> None:
    assert client.post(ACTIVITIES, json=_payload()).status_code == 401


def test_create_activity_validation_error(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    bad = _payload(ends_at="2029-01-01T00:00:00Z")  # ends before starts
    assert client.post(ACTIVITIES, json=bad, headers=_auth(host)).status_code == 422


def test_list_activities_paginated(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    for i in range(3):
        client.post(ACTIVITIES, json=_payload(title=f"Activity {i}"), headers=_auth(host))
    resp = client.get(ACTIVITIES, params={"limit": 2, "offset": 0})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def test_filter_activities_by_category(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    client.post(ACTIVITIES, json=_payload(title="Ball", category="sports"), headers=_auth(host))
    client.post(ACTIVITIES, json=_payload(title="Chess", category="games"), headers=_auth(host))
    resp = client.get(ACTIVITIES, params={"category": "games"})
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Chess"


def test_filter_activities_by_skill_level(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    client.post(ACTIVITIES, json=_payload(title="Beginner Run", skill_level="beginner"), headers=_auth(host))
    client.post(ACTIVITIES, json=_payload(title="Expert Run", skill_level="expert"), headers=_auth(host))
    resp = client.get(ACTIVITIES, params={"skill_level": "expert"})
    assert resp.status_code == 200, resp.text
    assert [a["title"] for a in resp.json()["items"]] == ["Expert Run"]


def test_search_activities_by_title(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    client.post(ACTIVITIES, json=_payload(title="Sunrise Hiking"), headers=_auth(host))
    client.post(ACTIVITIES, json=_payload(title="Board Game Night"), headers=_auth(host))
    resp = client.get(ACTIVITIES, params={"search": "Hiking"})
    assert resp.status_code == 200, resp.text
    assert [a["title"] for a in resp.json()["items"]] == ["Sunrise Hiking"]


def test_get_activity_ok(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    resp = client.get(f"{ACTIVITIES}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_activity_not_found_404(client: TestClient) -> None:
    resp = client.get(f"{ACTIVITIES}/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_patch_activity_by_host_ok(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    resp = client.patch(
        f"{ACTIVITIES}/{created['id']}", json={"title": "Updated Title"}, headers=_auth(host)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "Updated Title"


def test_patch_activity_non_host_forbidden_403(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    other = _register(client, "other@example.com", "other")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    resp = client.patch(
        f"{ACTIVITIES}/{created['id']}", json={"title": "Hijacked"}, headers=_auth(other)
    )
    assert resp.status_code == 403


def test_delete_activity_non_host_forbidden_403(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    other = _register(client, "other@example.com", "other")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    assert client.delete(f"{ACTIVITIES}/{created['id']}", headers=_auth(other)).status_code == 403


def test_delete_activity_by_host_204(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    assert client.delete(f"{ACTIVITIES}/{created['id']}", headers=_auth(host)).status_code == 204
    assert client.get(f"{ACTIVITIES}/{created['id']}").status_code == 404


def test_join_activity_ok(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    resp = client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "confirmed"
    detail = client.get(f"{ACTIVITIES}/{created['id']}").json()
    assert detail["participant_count"] == 2


def test_join_activity_full_goes_to_waitlist(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    # max=1: the host already occupies the only confirmed slot.
    created = client.post(
        ACTIVITIES, json=_payload(max_participants=1), headers=_auth(host)
    ).json()
    resp = client.post(
        f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"])
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "waitlisted"
    # Real state change persisted: the joiner is a WAITLISTED participant.
    participants = client.get(f"{ACTIVITIES}/{created['id']}/participants").json()
    joiner_row = next(p for p in participants if p["status"] == "waitlisted")
    assert joiner_row["user_id"] == joiner["user"]["id"]


def test_leave_promotes_first_waitlisted_to_confirmed(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    first = _register_body(client, "first@example.com", "first")
    second = _register_body(client, "second@example.com", "second")
    created = client.post(
        ACTIVITIES, json=_payload(max_participants=2), headers=_auth(host)
    ).json()
    aid = created["id"]
    # Host holds slot 1; first holds slot 2 (confirmed); second is waitlisted.
    assert (
        client.post(f"{ACTIVITIES}/{aid}/join", headers=_auth(first["tokens"])).json()["status"]
        == "confirmed"
    )
    assert (
        client.post(f"{ACTIVITIES}/{aid}/join", headers=_auth(second["tokens"])).json()["status"]
        == "waitlisted"
    )
    # first leaves -> frees a confirmed slot -> second is promoted.
    assert (
        client.post(f"{ACTIVITIES}/{aid}/leave", headers=_auth(first["tokens"])).status_code == 204
    )
    participants = client.get(f"{ACTIVITIES}/{aid}/participants").json()
    statuses = {p["user_id"]: p["status"] for p in participants}
    assert statuses[second["user"]["id"]] == "confirmed"
    assert first["user"]["id"] not in statuses
    assert len(participants) == 2  # host + promoted second


def test_create_activity_with_sport_and_variant(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    payload = _payload(
        title="Friday Futsal",
        sport_slug="futsal",
        sport_variant="5v5",
        sport_format="ranked",
    )
    resp = client.post(ACTIVITIES, json=payload, headers=_auth(host))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["sport_slug"] == "futsal"
    assert body["sport_category"] == "team"
    assert body["sport_variant"] == "5v5"
    assert body["sport_format"] == "ranked"
    # Catalog metrics are tracked by default for the chosen sport.
    assert body["sport_metrics"]


def test_create_activity_rejects_unknown_sport(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    resp = client.post(
        ACTIVITIES, json=_payload(sport_slug="quidditch"), headers=_auth(host)
    )
    assert resp.status_code == 422, resp.text


def test_create_activity_rejects_invalid_variant_for_sport(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    # "doubles" is valid for padel but not for futsal (4v4,5v5).
    resp = client.post(
        ACTIVITIES,
        json=_payload(sport_slug="futsal", sport_variant="doubles"),
        headers=_auth(host),
    )
    assert resp.status_code == 422, resp.text


def test_join_activity_twice_conflict(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner))
    assert client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner)).status_code == 409


def test_join_private_activity_forbidden_403(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(
        ACTIVITIES, json=_payload(visibility="private"), headers=_auth(host)
    ).json()
    assert client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner)).status_code == 403


def test_leave_activity_ok(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner))
    resp = client.post(f"{ACTIVITIES}/{created['id']}/leave", headers=_auth(joiner))
    assert resp.status_code == 204
    assert client.get(f"{ACTIVITIES}/{created['id']}").json()["participant_count"] == 1


def test_list_participants(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register(client, "joiner@example.com", "joiner")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner))
    resp = client.get(f"{ACTIVITIES}/{created['id']}/participants")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


def test_join_activity_not_found_404(client: TestClient) -> None:
    joiner = _register(client, "joiner@example.com", "joiner")
    resp = client.post(f"{ACTIVITIES}/{uuid.uuid4()}/join", headers=_auth(joiner))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# "Aktivitas Saya" - GET /activities/mine (real, caller-scoped history)
# ---------------------------------------------------------------------------

MINE = f"{ACTIVITIES}/mine"
VENUES = "/api/v1/venues"


def _mine(client: TestClient, tokens: dict, **params) -> dict:
    resp = client.get(MINE, headers=_auth(tokens), params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_mine_requires_auth(client: TestClient) -> None:
    assert client.get(MINE).status_code == 401


def test_mine_upcoming_includes_confirmed_join(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    created = client.post(
        ACTIVITIES, json=_payload(title="Future Padel", sport_slug="padel"), headers=_auth(host)
    ).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))

    body = _mine(client, joiner["tokens"])
    upcoming = body["groups"]["upcoming"]
    assert [a["id"] for a in upcoming] == [created["id"]]
    item = upcoming[0]
    assert item["state"] == "upcoming"
    assert item["participation_status"] == "confirmed"
    assert item["is_host"] is False
    assert item["sport_slug"] == "padel"
    assert item["sport_label"] == "Padel"
    assert item["starts_at"]
    assert body["groups"]["hosting"] == []


def test_mine_waitlisted(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    created = client.post(
        ACTIVITIES, json=_payload(max_participants=1), headers=_auth(host)
    ).json()
    resp = client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))
    assert resp.json()["status"] == "waitlisted"

    body = _mine(client, joiner["tokens"])
    waitlisted = body["groups"]["waitlisted"]
    assert [a["id"] for a in waitlisted] == [created["id"]]
    assert waitlisted[0]["participation_status"] == "waitlisted"
    assert waitlisted[0]["state"] == "waitlisted"
    assert body["groups"]["upcoming"] == []


def test_mine_past_reflects_no_show_outcome(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    created = client.post(
        ACTIVITIES,
        json=_payload(
            title="Last Year Football",
            starts_at="2020-01-01T10:00:00Z",
            ends_at="2020-01-01T12:00:00Z",
        ),
        headers=_auth(host),
    ).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))

    body = _mine(client, joiner["tokens"])
    past_items = body["groups"]["past"]
    assert [a["id"] for a in past_items] == [created["id"]]
    assert past_items[0]["state"] == "past"
    assert past_items[0]["attendance"] == "no_show"


def test_mine_past_reflects_attended_outcome(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    now = datetime.now(UTC)
    created = client.post(
        ACTIVITIES,
        json=_payload(
            title="Just Started Padel",
            sport_slug="padel",
            starts_at=(now - timedelta(minutes=30)).isoformat(),
            ends_at=(now + timedelta(minutes=30)).isoformat(),
        ),
        headers=_auth(host),
    ).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))
    ci = client.post(
        f"{ACTIVITIES}/{created['id']}/checkin", json={}, headers=_auth(joiner["tokens"])
    )
    assert ci.status_code == 201, ci.text

    body = _mine(client, joiner["tokens"])
    past_items = body["groups"]["past"]
    assert [a["id"] for a in past_items] == [created["id"]]
    assert past_items[0]["attendance"] == "attended"
    assert past_items[0]["participation_status"] == "attended"


def test_mine_cancelled_activity_is_past_cancelled(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    created = client.post(ACTIVITIES, json=_payload(), headers=_auth(host)).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))
    cancelled = client.post(f"{ACTIVITIES}/{created['id']}/cancel", headers=_auth(host))
    assert cancelled.status_code == 200

    body = _mine(client, joiner["tokens"])
    past_items = body["groups"]["past"]
    assert [a["id"] for a in past_items] == [created["id"]]
    assert past_items[0]["attendance"] == "cancelled"


def test_mine_hosting(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    created = client.post(
        ACTIVITIES, json=_payload(title="My Hosted Run", sport_slug="running"), headers=_auth(host)
    ).json()

    body = _mine(client, host)
    hosting = body["groups"]["hosting"]
    assert [a["id"] for a in hosting] == [created["id"]]
    assert hosting[0]["is_host"] is True
    assert hosting[0]["state"] == "hosting"
    assert hosting[0]["sport_label"] == "Lari"


def test_mine_scoped_to_caller(client: TestClient) -> None:
    a = _register(client, "a@example.com", "usera")
    b = _register_body(client, "b@example.com", "userb")
    created = client.post(ACTIVITIES, json=_payload(title="A Only"), headers=_auth(a)).json()

    body = _mine(client, b["tokens"])
    assert body["total"] == 0
    assert body["items"] == []
    leaked = [item["id"] for bucket in body["groups"].values() for item in bucket]
    assert created["id"] not in leaked


def test_mine_filter_by_sport(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    client.post(
        ACTIVITIES, json=_payload(title="Futsal Night", sport_slug="futsal"), headers=_auth(host)
    )
    client.post(
        ACTIVITIES, json=_payload(title="Padel Night", sport_slug="padel"), headers=_auth(host)
    )

    body = _mine(client, host, sport="futsal")
    assert body["total"] == 1
    assert [a["title"] for a in body["items"]] == ["Futsal Night"]
    assert [a["title"] for a in body["groups"]["hosting"]] == ["Futsal Night"]


def test_mine_filter_by_status(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    joiner = _register_body(client, "joiner@example.com", "joiner")
    created = client.post(
        ACTIVITIES, json=_payload(max_participants=1), headers=_auth(host)
    ).json()
    client.post(f"{ACTIVITIES}/{created['id']}/join", headers=_auth(joiner["tokens"]))

    body = _mine(client, joiner["tokens"], status="waitlisted")
    assert body["total"] == 1
    assert body["items"][0]["state"] == "waitlisted"

    empty = _mine(client, joiner["tokens"], status="upcoming")
    assert empty["total"] == 0
    assert empty["items"] == []


def test_mine_pagination(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    for i in range(3):
        client.post(ACTIVITIES, json=_payload(title=f"Hosted {i}"), headers=_auth(host))

    first = _mine(client, host, limit=2, offset=0)
    assert first["total"] == 3
    assert first["limit"] == 2
    assert first["offset"] == 0
    assert len(first["items"]) == 2

    second = _mine(client, host, limit=2, offset=2)
    assert second["total"] == 3
    assert len(second["items"]) == 1


def test_mine_carries_sport_and_venue_labels(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    venue = client.post(
        VENUES,
        json={
            "name": "Padel Arena",
            "city": "Jakarta",
            "sport_slugs": ["padel"],
            "courts": [{"name": "Court 1", "resource_label": "Court"}],
        },
        headers=_auth(host),
    ).json()
    court_id = client.get(f"{VENUES}/{venue['id']}/courts").json()[0]["id"]
    client.post(
        ACTIVITIES,
        json=_payload(
            title="Padel at Arena",
            sport_slug="padel",
            venue_id=venue["id"],
            venue_court_id=court_id,
        ),
        headers=_auth(host),
    )

    item = _mine(client, host)["groups"]["hosting"][0]
    assert item["sport_label"] == "Padel"
    assert item["sport_label_en"] == "Padel"
    assert item["venue_label"] == "Padel Arena"
    assert item["court_label"] == "Court 1"


def test_mine_past_hosted_activity_is_past_not_hosting(client: TestClient) -> None:
    """A *finished* activity the caller hosts must not be a live "hosting" item.

    Regression: the flat "Aktivitas Saya" page used to lead with stale past
    hosted events because hosting outranked the time check.
    """
    host = _register(client, "host@example.com", "host")
    past = client.post(
        ACTIVITIES,
        json=_payload(
            title="Old Hosted Run",
            starts_at="2020-01-01T10:00:00Z",
            ends_at="2020-01-01T12:00:00Z",
        ),
        headers=_auth(host),
    ).json()
    future = client.post(
        ACTIVITIES, json=_payload(title="Next Hosted Run"), headers=_auth(host)
    ).json()

    body = _mine(client, host)
    assert [a["id"] for a in body["groups"]["hosting"]] == [future["id"]]
    assert [a["id"] for a in body["groups"]["past"]] == [past["id"]]
    # Flat page: upcoming/ongoing leads; the finished one trails.
    assert [a["id"] for a in body["items"]] == [future["id"], past["id"]]


def test_mine_active_only_drops_past(client: TestClient) -> None:
    """?active_only=true returns only upcoming/ongoing (empty when none)."""
    host = _register(client, "host@example.com", "host")
    client.post(
        ACTIVITIES,
        json=_payload(
            title="Old Hosted Run",
            starts_at="2020-01-01T10:00:00Z",
            ends_at="2020-01-01T12:00:00Z",
        ),
        headers=_auth(host),
    )
    only_past = _mine(client, host, active_only="true")
    assert only_past["total"] == 0
    assert only_past["items"] == []

    future = client.post(
        ACTIVITIES, json=_payload(title="Next Hosted Run"), headers=_auth(host)
    ).json()
    both = _mine(client, host, active_only="true")
    assert [a["id"] for a in both["items"]] == [future["id"]]
    # groups still expose the full partition regardless of active_only.
    assert len(both["groups"]["past"]) == 1
