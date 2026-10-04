"""MMR engine tests: Elo maths, provisional K, team averaging, leaderboard.

Pure-function tests need no DB; integration tests exercise the full
create -> submit -> verify -> MMR-applied -> leaderboard path through the API.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.models.enums import ParticipantStatus
from app.models.activity import Activity, ActivityParticipant
from app.models.enums import ActivityCategory, ActivityVisibility, SkillLevel
from app.services.mmr_service import (
    BASE_K,
    DEFAULT_RATING,
    PROVISIONAL_K,
    MmrService,
    expected_score,
    mmr_scope_key,
    provisional_k_factor,
    score_from_scores,
    team_average,
    team_delta,
    update,
)

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


# --------------------------------------------------------------------------- #
# Pure-function maths                                                         #
# --------------------------------------------------------------------------- #
def test_expected_score_equal_ratings_is_half() -> None:
    assert expected_score(1200.0, 1200.0) == pytest.approx(0.5)


def test_expected_score_is_symmetric_and_bounded() -> None:
    a, b = 1600.0, 1200.0  # a 400-point gap
    e_a = expected_score(a, b)
    e_b = expected_score(b, a)
    assert e_a + e_b == pytest.approx(1.0)
    assert 0.0 < e_a < 1.0
    # A 400-point edge is the classic ~0.909 / ~0.091 split.
    assert e_a == pytest.approx(10 / 11, abs=1e-6)


def test_win_raises_winner_and_lowers_loser() -> None:
    new_a, new_b = update(1200.0, 1200.0, score_a=1.0, k=32.0)
    assert new_a > 1200.0
    assert new_b < 1200.0
    # Zero-sum: total rating is conserved.
    assert (new_a + new_b) == pytest.approx(2400.0)


def test_loss_lowers_and_upsets_swing_harder() -> None:
    loser, winner = update(1200.0, 1200.0, score_a=0.0, k=32.0)
    assert loser < 1200.0 and winner > 1200.0
    # An upset (low beats high) moves the lower player further than a favourite win.
    underdog_gain, _ = update(1000.0, 1400.0, score_a=1.0, k=32.0)
    favourite_gain, _ = update(1400.0, 1000.0, score_a=1.0, k=32.0)
    assert (underdog_gain - 1000.0) > (favourite_gain - 1400.0)


def test_draw_between_equal_players_is_a_no_op() -> None:
    new_a, new_b = update(1200.0, 1200.0, score_a=0.5, k=32.0)
    assert new_a == pytest.approx(1200.0)
    assert new_b == pytest.approx(1200.0)


def test_provisional_k_factor_threshold() -> None:
    assert provisional_k_factor(0) == PROVISIONAL_K
    assert provisional_k_factor(9) == PROVISIONAL_K
    assert provisional_k_factor(10) == BASE_K
    assert provisional_k_factor(50) == BASE_K
    assert PROVISIONAL_K > BASE_K


def test_team_average_and_delta() -> None:
    assert team_average([1200.0, 1400.0]) == pytest.approx(1300.0)
    assert team_average([]) == DEFAULT_RATING
    # Equal-average teams: the same delta applies to every member of the side.
    delta = team_delta([1200.0, 1400.0], [1300.0, 1300.0], score_a=1.0, k=32.0)
    assert delta > 0.0


def test_score_from_scores_mapping() -> None:
    assert score_from_scores(3, 1) == 1.0
    assert score_from_scores(1, 3) == 0.0
    assert score_from_scores(2, 2) == 0.5


# --------------------------------------------------------------------------- #
# DB-integrated: create -> submit -> verify -> MMR -> leaderboard              #
# --------------------------------------------------------------------------- #
def _create_activity(
    client: TestClient,
    tokens: dict,
    title: str = "Ranked Padel",
    sport_slug: str | None = "padel",
) -> str:
    payload: dict = {
        "title": title,
        "skill_level": "intermediate",
        "visibility": "public",
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T12:00:00Z",
        "max_participants": 8,
        "currency": "EUR",
    }
    if sport_slug is not None:
        payload["sport_slug"] = sport_slug
    else:
        payload["category"] = "sports"
    resp = client.post(
        "/api/v1/activities",
        json=payload,
        headers=_auth(tokens),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _record_and_verify(
    client: TestClient,
    host: dict,
    guest: dict,
    activity_id: str,
    team_a_score: int = 5,
    team_b_score: int = 3,
) -> tuple[str, dict]:
    """Full flow: host records + submits, guest verifies -> returns (match_id, result)."""
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]
    # Guest must already be an activity participant to be listed in a match.
    client.post(f"/api/v1/activities/{activity_id}/join", headers=_auth(guest))
    match_id = client.post(
        f"/api/v1/activities/{activity_id}/matches",
        json={
            "participants": [
                {"user_id": host_id, "team": 0, "score": team_a_score},
                {"user_id": guest_id, "team": 1, "score": team_b_score},
            ]
        },
        headers=_auth(host),
    ).json()["id"]
    result = client.post(
        f"/api/v1/matches/{match_id}/result",
        json={"team_a_score": team_a_score, "team_b_score": team_b_score},
        headers=_auth(host),
    ).json()
    verify = client.post(
        f"/api/v1/matches/{match_id}/verify",
        json={"result_id": result["id"], "confirmed": True},
        headers=_auth(guest),
    )
    assert verify.status_code == 200, verify.text
    return match_id, verify.json()


def test_full_flow_applies_mmr_and_ranks_leaderboard(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]

    activity_id = _create_activity(client, host)
    assert (
        client.post(f"/api/v1/activities/{activity_id}/join", headers=_auth(guest)).status_code
        == 200
    )

    # Host records the match (host on team A, guest on team B).
    resp = client.post(
        f"/api/v1/activities/{activity_id}/matches",
        json={
            "participants": [
                {"user_id": host_id, "team": 0, "score": 5},
                {"user_id": guest_id, "team": 1, "score": 3},
            ]
        },
        headers=_auth(host),
    )
    assert resp.status_code == 201, resp.text
    match_id = resp.json()["id"]

    # Host submits the result -> PENDING_VERIFICATION (status=submitted).
    resp = client.post(
        f"/api/v1/matches/{match_id}/result",
        json={"team_a_score": 5, "team_b_score": 3},
        headers=_auth(host),
    )
    assert resp.status_code == 201, resp.text
    result = resp.json()
    assert result["status"] == "submitted"  # pending verification
    result_id = result["id"]

    # Submitter may not verify their own result (server-enforced).
    assert (
        client.post(
            f"/api/v1/matches/{match_id}/verify",
            json={"result_id": result_id, "confirmed": True},
            headers=_auth(host),
        ).status_code
        == 403
    )

    # Guest confirms -> majority reached -> VERIFIED + MMR applied.
    resp = client.post(
        f"/api/v1/matches/{match_id}/verify",
        json={"result_id": result_id, "confirmed": True},
        headers=_auth(guest),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "verified"
    assert resp.json()["mmr_applied"] is True

    # Winner's rating rose, loser's fell, both from the 1200 default.
    host_ratings = client.get(
        f"/api/v1/users/{host_id}/ratings", headers=_auth(host)
    ).json()
    guest_ratings = client.get(
        f"/api/v1/users/{guest_id}/ratings", headers=_auth(guest)
    ).json()
    host_rating = host_ratings["ratings"][0]
    guest_rating = guest_ratings["ratings"][0]
    assert host_rating["category"] == "racket"
    assert host_rating["sport_slug"] == "padel"
    assert host_rating["rating"] > DEFAULT_RATING
    assert guest_rating["rating"] < DEFAULT_RATING
    assert host_rating["wins"] == 1
    assert guest_rating["losses"] == 1
    assert len(host_ratings["history"]) == 1
    assert host_ratings["history"][0]["delta"] > 0

    # Leaderboard is ranked, winner first.
    board = client.get(
        f"/api/v1/activities/{activity_id}/leaderboard", headers=_auth(host)
    ).json()
    assert len(board) == 2
    assert board[0]["rank"] == 1
    assert board[0]["user_id"] == host_id
    assert board[0]["rating"] >= board[1]["rating"]
    assert board[1]["rank"] == 2


def test_only_host_may_create_match(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]
    activity_id = _create_activity(client, host)
    client.post(f"/api/v1/activities/{activity_id}/join", headers=_auth(guest))

    resp = client.post(
        f"/api/v1/activities/{activity_id}/matches",
        json={
            "participants": [
                {"user_id": host_id, "team": 0},
                {"user_id": guest_id, "team": 1},
            ]
        },
        headers=_auth(guest),  # not the host
    )
    assert resp.status_code == 403, resp.text


def test_non_participant_cannot_verify(client: TestClient) -> None:
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    outsider = _register(client, "outsider@example.com", "outsider")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]
    activity_id = _create_activity(client, host)
    client.post(f"/api/v1/activities/{activity_id}/join", headers=_auth(guest))

    match_id = client.post(
        f"/api/v1/activities/{activity_id}/matches",
        json={
            "participants": [
                {"user_id": host_id, "team": 0},
                {"user_id": guest_id, "team": 1},
            ]
        },
        headers=_auth(host),
    ).json()["id"]
    result_id = client.post(
        f"/api/v1/matches/{match_id}/result",
        json={"team_a_score": 1, "team_b_score": 0},
        headers=_auth(host),
    ).json()["id"]

    resp = client.post(
        f"/api/v1/matches/{match_id}/verify",
        json={"result_id": result_id, "confirmed": True},
        headers=_auth(outsider),
    )
    assert resp.status_code == 403, resp.text


# --------------------------------------------------------------------------- #
# Sport-specific MMR: per-sport isolation, gating, verify-only, leaderboards   #
# --------------------------------------------------------------------------- #
def test_mmr_is_per_sport_and_isolated(client: TestClient) -> None:
    """A rating gained in padel must not change the player's tennis rating."""
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]

    padel_id = _create_activity(client, host, "Padel night", sport_slug="padel")
    _record_and_verify(client, host, guest, padel_id)

    tennis_id = _create_activity(client, host, "Tennis night", sport_slug="tennis")
    _record_and_verify(client, host, guest, tennis_id)

    ratings = client.get(f"/api/v1/users/{host_id}/ratings", headers=_auth(host)).json()
    by_sport = {r["sport_slug"]: r for r in ratings["ratings"]}
    assert set(by_sport) == {"padel", "tennis"}
    # Both sports independently moved off the default - separate rows, separate math.
    assert by_sport["padel"]["rating"] > DEFAULT_RATING
    assert by_sport["tennis"]["rating"] > DEFAULT_RATING
    assert by_sport["padel"]["games_played"] == 1
    assert by_sport["tennis"]["games_played"] == 1
    assert by_sport["padel"]["id"] != by_sport["tennis"]["id"]


def test_rating_scope_key_isolates_sports() -> None:
    assert mmr_scope_key("padel", "racket") == "padel"
    assert mmr_scope_key("tennis", "racket") == "tennis"
    assert mmr_scope_key(None, "sports") == "category:sports"
    assert mmr_scope_key("padel", "racket") != mmr_scope_key("tennis", "racket")


def test_mmr_rejected_for_non_competitive_sport(client: TestClient) -> None:
    """A verified result in a non-competitive sport must not change MMR."""
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]

    # hiking is a catalog sport flagged competitive=False.
    activity_id = _create_activity(client, host, "Hike", sport_slug="hiking")
    _record_and_verify(client, host, guest, activity_id)

    ratings = client.get(f"/api/v1/users/{host_id}/ratings", headers=_auth(host)).json()
    assert ratings["ratings"] == []
    assert ratings["history"] == []


def test_mmr_unchanged_on_submit_changed_on_verify(client: TestClient) -> None:
    """MMR is applied only at VERIFIED - never on submit (server-enforced)."""
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]

    activity_id = _create_activity(client, host, "Padel", sport_slug="padel")
    client.post(f"/api/v1/activities/{activity_id}/join", headers=_auth(guest))

    match_id = client.post(
        f"/api/v1/activities/{activity_id}/matches",
        json={
            "participants": [
                {"user_id": host_id, "team": 0, "score": 5},
                {"user_id": guest_id, "team": 1, "score": 3},
            ]
        },
        headers=_auth(host),
    ).json()["id"]

    submitted = client.post(
        f"/api/v1/matches/{match_id}/result",
        json={"team_a_score": 5, "team_b_score": 3},
        headers=_auth(host),
    ).json()
    assert submitted["status"] == "submitted"
    assert submitted["mmr_applied"] is False

    # Nothing applied yet: no ratings, no history.
    mid = client.get(f"/api/v1/users/{host_id}/ratings", headers=_auth(host)).json()
    assert mid["ratings"] == []
    assert mid["history"] == []

    verified = client.post(
        f"/api/v1/matches/{match_id}/verify",
        json={"result_id": submitted["id"], "confirmed": True},
        headers=_auth(guest),
    ).json()
    assert verified["status"] == "verified"
    assert verified["mmr_applied"] is True

    after = client.get(f"/api/v1/users/{host_id}/ratings", headers=_auth(host)).json()
    assert len(after["ratings"]) == 1
    assert after["ratings"][0]["sport_slug"] == "padel"
    assert after["ratings"][0]["rating"] > DEFAULT_RATING
    assert len(after["history"]) == 1


def test_apply_result_rejects_unverified_status(client: TestClient, db_session: Session) -> None:
    """The service refuses to apply MMR to a merely-submitted result."""
    from app.models.enums import MatchResultStatus
    from app.models.match import MatchResult

    service = MmrService(db_session)
    result = MatchResult(
        match_id=uuid.uuid4(),
        submitted_by_id=uuid.uuid4(),
        status=MatchResultStatus.SUBMITTED,
        team_a_score=1,
        team_b_score=0,
        mmr_applied=False,
    )
    db_session.add(result)
    db_session.flush()
    with pytest.raises(ValidationError):
        service.apply_result(result)


def test_leaderboard_per_sport_and_unranked(client: TestClient) -> None:
    """Leaderboards are per sport; a player with no games is UNRANKED."""
    host = _register(client, "host@example.com", "host")
    guest = _register(client, "guest@example.com", "guest")
    third = _register(client, "third@example.com", "third")
    host_id = client.get("/api/v1/auth/me", headers=_auth(host)).json()["id"]
    guest_id = client.get("/api/v1/auth/me", headers=_auth(guest)).json()["id"]

    padel_id = _create_activity(client, host, "Padel", sport_slug="padel")
    client.post(f"/api/v1/activities/{padel_id}/join", headers=_auth(guest))
    _record_and_verify(client, host, guest, padel_id)

    # Host's padel board: ranked, host first (won).
    board = client.get(
        "/api/v1/sports/padel/leaderboard", headers=_auth(host)
    ).json()
    assert board["sport_slug"] == "padel"
    assert board["me"]["ranked"] is True
    assert board["me"]["rank"] == 1
    assert [e["user_id"] for e in board["entries"]] == [host_id, guest_id]
    assert board["entries"][0]["rank"] == 1
    assert board["entries"][0]["sport_slug"] == "padel"
    assert board["entries"][0]["rating"] >= board["entries"][1]["rating"]

    # Tennis has no verified matches -> empty board and an UNRANKED caller.
    tennis = client.get(
        "/api/v1/sports/tennis/leaderboard", headers=_auth(host)
    ).json()
    assert tennis["entries"] == []
    assert tennis["me"]["ranked"] is False
    assert tennis["me"]["rank"] is None
    assert tennis["me"]["rating"] is None

    # A player who never played padel is UNRANKED on the padel board too.
    third_board = client.get(
        "/api/v1/sports/padel/leaderboard", headers=_auth(third)
    ).json()
    assert third_board["me"]["ranked"] is False
    assert third_board["me"]["rank"] is None
    # ...but the board itself still shows the two ranked players.
    assert len(third_board["entries"]) == 2

    # Unknown sport -> 404.
    assert (
        client.get("/api/v1/sports/not-a-sport/leaderboard", headers=_auth(host)).status_code
        == 404
    )
