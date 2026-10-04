"""Tournament lifecycle tests: CRUD, registration, bracket, results, standings.

Covers the RBAC contract too - only the organizer (or an admin) may build the
bracket or advance results; anyone else gets a 403 from the server.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
TOURNAMENTS = "/api/v1/tournaments"


def _make_user(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER, json={"email": email, "username": username, "password": "RallyPass123"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create(client: TestClient, headers: dict, name: str = "Summer Open") -> dict:
    resp = client.post(
        TOURNAMENTS,
        headers=headers,
        json={"name": name, "max_entries": 4, "category": "sports"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_requires_auth(client: TestClient) -> None:
    assert client.post(TOURNAMENTS, json={"name": "Nope"}).status_code == 401


def test_create_and_get_tournament(client: TestClient) -> None:
    admin = _make_user(client, "org@example.com", "organizer")
    created = _create(client, _auth(admin["tokens"]))
    assert created["organizer_id"] == admin["user"]["id"]
    assert created["status"] == "draft"

    got = client.get(f"{TOURNAMENTS}/{created['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "Summer Open"


def test_list_tournaments(client: TestClient) -> None:
    admin = _make_user(client, "org2@example.com", "organizer2")
    _create(client, _auth(admin["tokens"]), "Alpha Cup")
    _create(client, _auth(admin["tokens"]), "Beta Cup")

    resp = client.get(TOURNAMENTS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert {t["name"] for t in body["items"]} == {"Alpha Cup", "Beta Cup"}


def test_register_and_unregister(client: TestClient) -> None:
    admin = _make_user(client, "org3@example.com", "organizer3")
    t = _create(client, _auth(admin["tokens"]))
    player = _make_user(client, "p1@example.com", "player1")
    ph = _auth(player["tokens"])

    reg = client.post(f"{TOURNAMENTS}/{t['id']}/register", headers=ph)
    assert reg.status_code == 201, reg.text
    assert reg.json()["user_id"] == player["user"]["id"]

    # Duplicate registration is rejected.
    dup = client.post(f"{TOURNAMENTS}/{t['id']}/register", headers=ph)
    assert dup.status_code in (400, 409)

    entries = client.get(f"{TOURNAMENTS}/{t['id']}/entries")
    assert entries.status_code == 200
    assert len(entries.json()) == 1

    unreg = client.delete(f"{TOURNAMENTS}/{t['id']}/register", headers=ph)
    assert unreg.status_code == 204
    assert client.get(f"{TOURNAMENTS}/{t['id']}/entries").json() == []


def test_bracket_requires_organizer_or_admin(client: TestClient) -> None:
    admin = _make_user(client, "org4@example.com", "organizer4")
    t = _create(client, _auth(admin["tokens"]))
    outsider = _make_user(client, "outsider@example.com", "outsider")
    oh = _auth(outsider["tokens"])

    client.post(f"{TOURNAMENTS}/{t['id']}/register", headers=oh)
    resp = client.post(f"{TOURNAMENTS}/{t['id']}/bracket", headers=oh)
    assert resp.status_code == 403


def _seed_players(client: TestClient, t_id: str, count: int) -> list[dict]:
    players = []
    for i in range(count):
        p = _make_user(client, f"tp{i}@example.com", f"tp{i}")
        client.post(f"{TOURNAMENTS}/{t_id}/register", headers=_auth(p["tokens"]))
        players.append(p)
    return players


def test_full_single_elimination_flow(client: TestClient, db_session: Session) -> None:
    admin = _make_user(client, "org5@example.com", "organizer5")
    # Promote the creator to ADMIN so they may advance results regardless of role.
    u = db_session.query(User).filter_by(email="org5@example.com").one()
    u.role = UserRole.ADMIN
    db_session.add(u)
    db_session.commit()
    login = client.post(LOGIN, json={"email": "org5@example.com", "password": "RallyPass123"})
    headers = _auth(login.json()["tokens"])

    t = _create(client, headers, "Knockout")
    _seed_players(client, t["id"], 4)

    bracket = client.post(f"{TOURNAMENTS}/{t['id']}/bracket", headers=headers)
    assert bracket.status_code == 200, bracket.text
    body = bracket.json()
    assert body["rounds"] == 2
    assert len(body["matches"]) == 3  # 2 semis + 1 final

    # Advance every match the organizer knows about, round by round.
    for _ in range(10):  # bounded loop; each iteration settles pending fixtures
        pending = [
            m
            for m in client.get(f"{TOURNAMENTS}/{t['id']}/bracket").json()["matches"]
            if m["status"] == "pending" and m["home_entry_id"] and m["away_entry_id"]
        ]
        if not pending:
            break
        for m in pending:
            res = client.post(
                f"{TOURNAMENTS}/{t['id']}/results",
                headers=headers,
                json={
                    "bracket_match_id": m["id"],
                    "winner_entry_id": m["home_entry_id"],
                    "home_score": 2,
                    "away_score": 0,
                },
            )
            assert res.status_code == 200, res.text

    standings = client.get(f"{TOURNAMENTS}/{t['id']}/standings")
    assert standings.status_code == 200
    rows = standings.json()["standings"]
    assert len(rows) == 4
    # Exactly one champion (rank 1) and no pending fixtures remain.
    assert rows[0]["rank"] == 1
    final = client.get(f"{TOURNAMENTS}/{t['id']}/bracket").json()["matches"]
    assert all(m["status"] == "completed" for m in final)


def test_result_rejects_non_organizer(client: TestClient) -> None:
    admin = _make_user(client, "org6@example.com", "organizer6")
    t = _create(client, _auth(admin["tokens"]))
    _seed_players(client, t["id"], 2)
    client.post(f"{TOURNAMENTS}/{t['id']}/bracket", headers=_auth(admin["tokens"]))

    outsider = _make_user(client, "outsider2@example.com", "outsider2")
    oh = _auth(outsider["tokens"])
    match = client.get(f"{TOURNAMENTS}/{t['id']}/bracket").json()["matches"][0]
    resp = client.post(
        f"{TOURNAMENTS}/{t['id']}/results",
        headers=oh,
        json={"bracket_match_id": match["id"], "winner_entry_id": match["home_entry_id"]},
    )
    assert resp.status_code == 403


def test_bracket_requires_min_two_entries(client: TestClient) -> None:
    admin = _make_user(client, "org7@example.com", "organizer7")
    t = _create(client, _auth(admin["tokens"]))
    resp = client.post(f"{TOURNAMENTS}/{t['id']}/bracket", headers=_auth(admin["tokens"]))
    assert resp.status_code in (400, 409)


def test_get_unknown_tournament_404(client: TestClient) -> None:
    resp = client.get(f"{TOURNAMENTS}/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
