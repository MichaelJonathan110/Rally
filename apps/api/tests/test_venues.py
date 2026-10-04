"""Venue API tests: create with courts, list/filter, owner-only writes, 404s."""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

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


def _payload(**overrides) -> dict:
    base = {
        "name": "Riverside Sports Park",
        "description": "Outdoor courts by the river",
        "address_line": "An der Spree 1",
        "city": "Berlin",
        "country": "DE",
        "latitude": 52.52,
        "longitude": 13.405,
        "timezone": "Europe/Berlin",
        "courts": [
            {
                "name": "Court 1",
                "surface": "grass",
                "capacity": 4,
                "hourly_price_cents": 2000,
                "availability": [
                    {"weekday": 0, "opens_at": "08:00:00", "closes_at": "22:00:00"}
                ],
            }
        ],
    }
    base.update(overrides)
    return base


def test_create_venue_with_courts_201(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.post(VENUES, json=_payload(), headers=_auth(owner))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Riverside Sports Park"
    assert body["city"] == "Berlin"
    assert body["court_count"] == 1
    assert body["owner_id"]


def test_create_venue_requires_auth(client: TestClient) -> None:
    assert client.post(VENUES, json=_payload()).status_code == 401


def test_create_venue_validation_error(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    bad = _payload(latitude=999)
    assert client.post(VENUES, json=bad, headers=_auth(owner)).status_code == 422


def test_list_venues_paginated(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    for i in range(3):
        client.post(VENUES, json=_payload(name=f"Venue {i}"), headers=_auth(owner))
    resp = client.get(VENUES, params={"limit": 2})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_filter_venues_by_city(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    client.post(VENUES, json=_payload(name="Berlin Court", city="Berlin"), headers=_auth(owner))
    client.post(VENUES, json=_payload(name="Munich Court", city="Munich"), headers=_auth(owner))
    resp = client.get(VENUES, params={"city": "Munich"})
    assert resp.status_code == 200, resp.text
    assert [v["name"] for v in resp.json()["items"]] == ["Munich Court"]


def test_get_venue_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.get(f"{VENUES}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_venue_not_found_404(client: TestClient) -> None:
    assert client.get(f"{VENUES}/{uuid.uuid4()}").status_code == 404


def test_patch_venue_owner_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.patch(
        f"{VENUES}/{created['id']}", json={"name": "Renamed Park"}, headers=_auth(owner)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed Park"


def test_patch_venue_non_owner_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    other = _register(client, "other@example.com", "other")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.patch(
        f"{VENUES}/{created['id']}", json={"name": "Hijack"}, headers=_auth(other)
    )
    assert resp.status_code == 403


def test_patch_venue_not_found_404(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.patch(
        f"{VENUES}/{uuid.uuid4()}", json={"name": "Ghost"}, headers=_auth(owner)
    )
    assert resp.status_code == 404


def test_list_courts(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.get(f"{VENUES}/{created['id']}/courts")
    assert resp.status_code == 200, resp.text
    courts = resp.json()
    assert len(courts) == 1
    assert courts[0]["name"] == "Court 1"
    assert len(courts[0]["availability"]) == 1


def test_list_courts_venue_not_found_404(client: TestClient) -> None:
    assert client.get(f"{VENUES}/{uuid.uuid4()}/courts").status_code == 404


def test_add_court_owner_ok(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.post(
        f"{VENUES}/{created['id']}/courts",
        json={"name": "Court 2", "surface": "clay", "capacity": 4, "hourly_price_cents": 2500},
        headers=_auth(owner),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["name"] == "Court 2"
    assert len(client.get(f"{VENUES}/{created['id']}/courts").json()) == 2


def test_add_court_non_owner_forbidden_403(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    other = _register(client, "other@example.com", "other")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.post(
        f"{VENUES}/{created['id']}/courts",
        json={"name": "Sneaky Court"},
        headers=_auth(other),
    )
    assert resp.status_code == 403


def test_add_court_duplicate_name_400(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_payload(), headers=_auth(owner)).json()
    resp = client.post(
        f"{VENUES}/{created['id']}/courts",
        json={"name": "Court 1"},
        headers=_auth(owner),
    )
    assert resp.status_code == 400, resp.text


# --- sport-awareness -------------------------------------------------------
def _sport_payload(**overrides) -> dict:
    """A padel venue: primary name + city + sport slugs + typed resources."""
    base = {
        "name": "RALLY Padel Arena",
        "city": "Tangerang",
        "country": "ID",
        "category": "sports",
        "timezone": "Asia/Jakarta",
        "venue_kind": "court",
        "sport_slugs": ["padel"],
        "courts": [
            {
                "name": "Court 1",
                "surface": "artificial",
                "capacity": 4,
                "hourly_price_cents": 200000,
                "venue_kind": "court",
                "resource_label": "Court",
                "availability": [
                    {"weekday": 0, "opens_at": "06:00:00", "closes_at": "22:00:00"},
                    {"weekday": 1, "opens_at": "06:00:00", "closes_at": "22:00:00"},
                ],
            }
        ],
    }
    base.update(overrides)
    return base


def test_venue_payload_is_sport_aware(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    resp = client.post(VENUES, json=_sport_payload(), headers=_auth(owner))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # primary name + city secondary
    assert body["name"] == "RALLY Padel Arena"
    assert body["location"] == "Tangerang, ID"
    # supported sport slugs + venue_kind
    assert body["sport_slugs"] == ["padel"]
    assert body["venue_kind"] == "court"
    # resources typed by venue_kind with label
    assert len(body["resources"]) == 1
    resource = body["resources"][0]
    assert resource["kind"] == "court"
    assert resource["label"] == "Court"
    # availability generated per RESOURCE
    assert len(resource["availability"]) == 2
    summary = body["availability"]
    assert summary["resource_count"] == 1
    assert summary["resources_with_windows"] == 1
    assert summary["total_windows"] == 2
    assert summary["open_weekdays"] == [0, 1]


def test_resources_endpoint_typed_by_venue_kind(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_sport_payload(), headers=_auth(owner)).json()
    resp = client.get(f"{VENUES}/{created['id']}/resources")
    assert resp.status_code == 200, resp.text
    resources = resp.json()
    assert len(resources) == 1
    assert resources[0]["kind"] == "court"
    assert resources[0]["label"] == "Court"
    assert len(resources[0]["availability"]) == 2


def test_availability_endpoint_summarises_per_resource(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(VENUES, json=_sport_payload(), headers=_auth(owner)).json()
    resp = client.get(f"{VENUES}/{created['id']}/availability")
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["resource_count"] == 1
    assert summary["total_windows"] == 2
    assert summary["earliest_open"] == "06:00:00"
    assert summary["latest_close"] == "22:00:00"


def test_availability_endpoint_404_for_unknown_venue(client: TestClient) -> None:
    assert client.get(f"{VENUES}/{uuid.uuid4()}/availability").status_code == 404


def test_court_inherits_venue_kind_when_omitted(client: TestClient) -> None:
    owner = _register(client, "owner@example.com", "owner")
    created = client.post(
        VENUES,
        json={
            "name": "RALLY Futsal Dome Surabaya",
            "city": "Surabaya",
            "country": "ID",
            "timezone": "Asia/Jakarta",
            "sport_slugs": ["futsal"],
        },
        headers=_auth(owner),
    ).json()
    # venue_kind derived from the sport slug via the sports catalog
    assert created["venue_kind"] == "field"
    resp = client.post(
        f"{VENUES}/{created['id']}/courts",
        json={"name": "Field 1", "surface": "sintetis", "capacity": 10,
              "hourly_price_cents": 150000},
        headers=_auth(owner),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["venue_kind"] == "field"


def test_catalog_venues_carry_real_names_city_and_sports() -> None:
    from app.core.venue_catalog import VENUE_BY_NAME

    venue = VENUE_BY_NAME["RALLY Padel Arena"]
    assert venue.primary_name == "RALLY Padel Arena"
    assert venue.location == "Tangerang, Indonesia"
    assert venue.sport_slugs == ("padel",)
    assert venue.venue_kind == "court"
    assert [(r.kind, r.label) for r in venue.resources] == [("court", "Court")]

    futsal = VENUE_BY_NAME["RALLY Futsal Dome Surabaya"]
    assert futsal.venue_kind == "field"
    assert [(r.kind, r.label) for r in futsal.resources] == [("field", "Field")]


def test_every_catalog_venue_resource_kind_is_a_real_venue_kind() -> None:
    """Each resource's (venue_kind, resource_label) pair must exist in sports.py."""
    from app.core.sports import SPORTS_PAYLOAD
    from app.core.venue_catalog import VENUE_CATALOG

    pairs = {(r["venue_kind"], r["resource_label"]) for r in SPORTS_PAYLOAD}
    kinds = {r["venue_kind"] for r in SPORTS_PAYLOAD}
    for venue in VENUE_CATALOG:
        for resource in venue.resources:
            assert resource.kind in kinds, f"unknown venue_kind {resource.kind!r}"
            assert (resource.kind, resource.label) in pairs, (
                f"unknown resource pair {(resource.kind, resource.label)!r}"
            )
