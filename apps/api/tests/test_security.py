"""Security-hardening tests: rate limiting, password policy, headers, CORS."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.rate_limit import auth_limiter

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


def _register(client: TestClient, email: str, username: str, password: str = "RallyPass123"):
    return client.post(
        REGISTER, json={"email": email, "username": username, "password": password}
    )


# --- password policy -------------------------------------------------------
def test_short_password_rejected(client: TestClient) -> None:
    resp = _register(client, "a@example.com", "user_a", password="Ab1!")
    assert resp.status_code == 422


def test_all_lowercase_password_rejected(client: TestClient) -> None:
    resp = _register(client, "b@example.com", "user_b", password="abcdefgh")
    assert resp.status_code == 422


def test_common_password_rejected(client: TestClient) -> None:
    resp = _register(client, "c@example.com", "user_c", password="Password123")
    assert resp.status_code == 422


def test_strong_password_accepted(client: TestClient) -> None:
    resp = _register(client, "d@example.com", "user_d", password="RallyPass123")
    assert resp.status_code == 201, resp.text


# --- rate limiting ---------------------------------------------------------
def test_login_rate_limited(client: TestClient) -> None:
    auth_limiter.reset()
    _register(client, "rl@example.com", "rl", password="RallyPass123")
    auth_limiter.reset()

    statuses = []
    for _ in range(15):
        r = client.post(
            LOGIN, json={"email": "rl@example.com", "password": "WrongPass123"}
        )
        statuses.append(r.status_code)
    assert 429 in statuses, statuses
    # Retry-After is advertised on the throttled response.
    throttled = [
        r
        for r in (
            client.post(LOGIN, json={"email": "rl@example.com", "password": "WrongPass123"})
            for _ in range(3)
        )
        if r.status_code == 429
    ]
    assert throttled and "Retry-After" in throttled[0].headers


def test_register_rate_limited(client: TestClient) -> None:
    auth_limiter.reset()
    statuses = []
    for i in range(15):
        r = _register(client, f"many{i}@example.com", f"many{i}")
        statuses.append(r.status_code)
    assert 429 in statuses, statuses


# --- security headers ------------------------------------------------------
def test_security_headers_present(client: TestClient) -> None:
    resp = client.get("/api/v1/tournaments")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# --- CORS ------------------------------------------------------------------
def test_cors_allows_preview_origin(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/tournaments", headers={"Origin": "http://127.0.0.1:4173"}
    )
    assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:4173"


def test_cors_preflight_login(client: TestClient) -> None:
    resp = client.options(
        LOGIN,
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:4173"
    allow_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    resp = client.get("/api/v1/tournaments", headers={"Origin": "http://evil.example.com"})
    assert resp.headers.get("access-control-allow-origin") is None
