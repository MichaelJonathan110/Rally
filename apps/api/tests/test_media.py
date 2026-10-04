"""Media upload + profile-avatar tests.

Covers the real upload pipeline end to end: validation (extension, size,
auth), on-disk persistence, and persisting the returned URL via PATCH
``/users/me`` so ``GET /users/me`` reflects it.
"""
from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

REGISTER = "/api/v1/auth/register"
UPLOAD = "/api/v1/media/upload"
ME = "/api/v1/users/me"

#: A real 1x1 transparent PNG.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _register(client: TestClient, email: str, username: str) -> dict:
    resp = client.post(
        REGISTER,
        json={"email": email, "username": username, "password": "RallyPass123"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['tokens']['access_token']}"}


@pytest.fixture()
def media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point uploads at a temp dir so tests never touch the real media store."""
    root = tmp_path / "media"
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(root))
    return root


def test_upload_png_persists_and_returns_url(
    client: TestClient, media_root: Path
) -> None:
    body = _register(client, "media-a@example.com", "media_a")
    resp = client.post(
        UPLOAD,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
        data={"purpose": "avatar"},
        headers=_auth(body),
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["url"].startswith("/media/avatar/")
    assert payload["url"].endswith(".png")
    assert payload["size"] == len(PNG_BYTES)
    assert payload["content_type"] == "image/png"

    stored = media_root / "avatar" / payload["filename"]
    assert stored.is_file()
    assert stored.read_bytes() == PNG_BYTES


def test_upload_rejects_oversize(
    client: TestClient, media_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = _register(client, "media-b@example.com", "media_b")
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 0)
    resp = client.post(
        UPLOAD,
        files={"file": ("big.png", PNG_BYTES, "image/png")},
        data={"purpose": "avatar"},
        headers=_auth(body),
    )
    assert resp.status_code == 413, resp.text
    # Nothing should have been left behind.
    assert not (media_root / "avatar").exists() or not any(
        (media_root / "avatar").iterdir()
    )


def test_upload_rejects_wrong_extension(client: TestClient, media_root: Path) -> None:
    body = _register(client, "media-c@example.com", "media_c")
    resp = client.post(
        UPLOAD,
        files={"file": ("notes.txt", b"not an image", "text/plain")},
        data={"purpose": "avatar"},
        headers=_auth(body),
    )
    assert resp.status_code == 400, resp.text


def test_upload_rejects_invalid_purpose(client: TestClient, media_root: Path) -> None:
    body = _register(client, "media-d@example.com", "media_d")
    resp = client.post(
        UPLOAD,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
        data={"purpose": "secret"},
        headers=_auth(body),
    )
    assert resp.status_code == 400, resp.text


def test_upload_requires_auth(client: TestClient, media_root: Path) -> None:
    resp = client.post(
        UPLOAD,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
        data={"purpose": "avatar"},
    )
    assert resp.status_code == 401, resp.text


def test_patch_me_persists_avatar_url(client: TestClient, media_root: Path) -> None:
    body = _register(client, "media-e@example.com", "media_e")
    headers = _auth(body)

    up = client.post(
        UPLOAD,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
        data={"purpose": "avatar"},
        headers=headers,
    )
    assert up.status_code == 201, up.text
    url = up.json()["url"]

    patched = client.patch(ME, json={"avatar_url": url}, headers=headers)
    assert patched.status_code == 200, patched.text
    assert patched.json()["profile"]["avatar_url"] == url

    got = client.get(ME, headers=headers)
    assert got.status_code == 200, got.text
    assert got.json()["profile"]["avatar_url"] == url


def test_delete_own_upload(client: TestClient, media_root: Path) -> None:
    body = _register(client, "media-f@example.com", "media_f")
    headers = _auth(body)
    up = client.post(
        UPLOAD,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
        data={"purpose": "avatar"},
        headers=headers,
    ).json()
    subdir, name = up["url"].rsplit("/", 2)[-2:]

    resp = client.delete(f"/api/v1/media/{subdir}/{name}", headers=headers)
    assert resp.status_code == 204, resp.text
    assert not (media_root / subdir / name).exists()
