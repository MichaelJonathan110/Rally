"""Health endpoint contract tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health_ok() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"status", "version", "db"}
    assert body["status"] == "ok"
    assert isinstance(body["version"], str)
    # No database is required for the process to answer; db is reported truthfully.
    assert body["db"] in {"ok", "down"}


def test_v1_health_ok() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["db"] in {"ok", "down"}


def test_brand_endpoint() -> None:
    resp = client.get("/api/v1/brand")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"]
    assert "tagline" in body
    assert set(body["theme"]) == {"primary", "accent", "radius"}


def test_openapi_available() -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "paths" in resp.json()
