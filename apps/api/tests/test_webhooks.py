"""Webhook tests: HMAC signature verification + idempotent status updates."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.services.payments import get_payment_provider
from app.services.payments.mock_provider import SIGNATURE_HEADER, MockProvider

BOOKINGS = "/api/v1/bookings"
VENUES = "/api/v1/venues"
WEBHOOK = "/api/v1/webhooks/payments"
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


def _make_court(client: TestClient, owner: dict, price: int = 2000) -> str:
    venue = client.post(
        VENUES,
        json={
            "name": "Webhook Venue",
            "city": "Berlin",
            "courts": [
                {
                    "name": "Court W",
                    "surface": "clay",
                    "capacity": 4,
                    "hourly_price_cents": price,
                }
            ],
        },
        headers=_auth(owner),
    ).json()
    return client.get(f"{VENUES}/{venue['id']}/courts").json()[0]["id"]


def _make_paid_booking(client: TestClient, owner: dict) -> dict:
    court_id = _make_court(client, owner)
    booking = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T11:00:00Z",
            "total_price_cents": 1500,
            "currency": "EUR",
        },
        headers=_auth(owner),
    ).json()
    payment = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "webhook-pay-1"},
        headers=_auth(owner),
    ).json()
    return payment


def test_webhook_rejects_missing_signature(client: TestClient) -> None:
    resp = client.post(f"{WEBHOOK}/mock", content=b"{}")
    assert resp.status_code == 400, resp.text


def test_webhook_rejects_bad_signature(client: TestClient) -> None:
    payload = json.dumps({"id": "evt_1", "status": "succeeded"}).encode()
    resp = client.post(
        f"{WEBHOOK}/mock",
        content=payload,
        headers={SIGNATURE_HEADER: "deadbeef"},
    )
    assert resp.status_code == 400, resp.text


def test_webhook_updates_status_idempotently(client: TestClient) -> None:
    owner = _register(client, "w1@example.com", "webhookowner1")
    payment = _make_paid_booking(client, owner)
    reference = payment["provider_reference"]

    provider = get_payment_provider("mock")
    assert isinstance(provider, MockProvider)

    # a refund webhook flips the local payment to refunded
    payload = json.dumps(
        {"id": "evt_refund_1", "status": "refunded", "payment_reference": reference}
    ).encode()
    signature = provider.sign_payload(payload)
    first = client.post(
        f"{WEBHOOK}/mock",
        content=payload,
        headers={SIGNATURE_HEADER: signature},
    )
    assert first.status_code == 200, first.text
    assert first.json()["applied"] is True
    assert first.json()["status"] == "refunded"

    # replaying the same event is a no-op (idempotent)
    second = client.post(
        f"{WEBHOOK}/mock",
        content=payload,
        headers={SIGNATURE_HEADER: signature},
    )
    assert second.status_code == 200, second.text
    assert second.json()["applied"] is False
    assert second.json().get("idempotent") is True


def test_webhook_unknown_provider_404(client: TestClient) -> None:
    resp = client.post(f"{WEBHOOK}/paypal", content=b"{}")
    assert resp.status_code == 404, resp.text


def test_webhook_unknown_reference_is_noop(client: TestClient) -> None:
    provider = get_payment_provider("mock")
    payload = json.dumps(
        {"id": "evt_x", "status": "succeeded", "payment_reference": "pi_unknown"}
    ).encode()
    resp = client.post(
        f"{WEBHOOK}/mock",
        content=payload,
        headers={SIGNATURE_HEADER: provider.sign_payload(payload)},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["applied"] is False
