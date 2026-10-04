"""Payments + cost-split + booking-flow tests.

Covers: equal/custom splits sum to the total, idempotent duplicate payment
returns the same row, refund on cancel, status transitions, and RBAC on cancel.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

BOOKINGS = "/api/v1/bookings"
VENUES = "/api/v1/venues"
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
            "name": "Payment Venue",
            "city": "Berlin",
            "courts": [
                {
                    "name": "Court P",
                    "surface": "clay",
                    "capacity": 4,
                    "hourly_price_cents": price,
                }
            ],
        },
        headers=_auth(owner),
    ).json()
    return client.get(f"{VENUES}/{venue['id']}/courts").json()[0]["id"]


def _make_booking(client: TestClient, owner: dict, **extra) -> dict:
    court_id = _make_court(client, owner)
    payload = {
        "venue_court_id": court_id,
        "starts_at": "2030-01-01T10:00:00Z",
        "ends_at": "2030-01-01T11:00:00Z",
        "currency": "EUR",
    }
    payload.update(extra)
    resp = client.post(BOOKINGS, json=payload, headers=_auth(owner))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_equal_split_sums_to_total(client: TestClient) -> None:
    owner = _register(client, "s1@example.com", "splitter1")
    mate = _register(client, "s2@example.com", "splitter2")
    booking = _make_booking(
        client,
        owner,
        total_price_cents=1000,
        split_between_user_ids=[mate["user"]["id"]],
    )
    shares = [s["share_cents"] for s in booking["splits"]]
    assert sum(shares) == 1000
    assert len(booking["splits"]) == 2  # owner + mate
    # remainder cent goes to the earliest share
    assert sorted(shares) == [500, 500]


def test_custom_split_must_sum_to_total(client: TestClient) -> None:
    owner = _register(client, "c1@example.com", "custom1")
    mate = _register(client, "c2@example.com", "custom2")
    booking = _make_booking(
        client,
        owner,
        total_price_cents=900,
        custom_splits=[
            {"user_id": owner["user"]["id"], "share_cents": 600},
            {"user_id": mate["user"]["id"], "share_cents": 300},
        ],
    )
    assert sum(s["share_cents"] for s in booking["splits"]) == 900


def test_custom_split_wrong_sum_rejected(client: TestClient) -> None:
    owner = _register(client, "w1@example.com", "wrong1")
    court_id = _make_court(client, owner)
    resp = client.post(
        BOOKINGS,
        json={
            "venue_court_id": court_id,
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T11:00:00Z",
            "total_price_cents": 900,
            "custom_splits": [
                {"user_id": owner["user"]["id"], "share_cents": 500},
            ],
        },
        headers=_auth(owner),
    )
    assert resp.status_code == 400, resp.text


def test_payment_confirms_booking_and_balance(client: TestClient) -> None:
    owner = _register(client, "p1@example.com", "payer1")
    booking = _make_booking(client, owner, total_price_cents=2000)
    assert booking["status"] == "pending"

    pay = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "pay-key-0001"},
        headers=_auth(owner),
    )
    assert pay.status_code == 201, pay.text
    assert pay.json()["status"] == "paid"
    assert pay.json()["provider"] == "mock"

    after = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert after["status"] == "confirmed"

    bal = client.get(f"{BOOKINGS}/{booking['id']}/balance", headers=_auth(owner)).json()
    assert bal["total_cents"] == 2000
    assert bal["paid_cents"] == 2000
    assert bal["outstanding_cents"] == 0


def test_duplicate_payment_is_idempotent(client: TestClient) -> None:
    owner = _register(client, "p2@example.com", "payer2")
    booking = _make_booking(client, owner, total_price_cents=1500)
    first = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "idem-abc-123"},
        headers=_auth(owner),
    )
    assert first.status_code == 201, first.text
    second = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "idem-abc-123"},
        headers=_auth(owner),
    )
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]  # same row, no double charge

    # only one PAID payment row exists for the booking
    detail = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    paid = [p for p in detail["payments"] if p["status"] == "paid"]
    assert len(paid) == 1


def test_cancel_paid_booking_triggers_refund(client: TestClient) -> None:
    owner = _register(client, "r1@example.com", "refund1")
    booking = _make_booking(client, owner, total_price_cents=1200)
    client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "refund-key-1"},
        headers=_auth(owner),
    )
    cancel = client.post(
        f"{BOOKINGS}/{booking['id']}/cancel", headers=_auth(owner)
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["status"] == "refunded"

    refunds = client.post(
        f"{BOOKINGS}/{booking['id']}/refund", headers=_auth(owner)
    )
    # already refunded by cancel -> idempotent, no new refund rows
    assert refunds.status_code == 200


def test_only_booker_or_host_may_cancel(client: TestClient) -> None:
    owner = _register(client, "o1@example.com", "ownerbooker")
    stranger = _register(client, "x1@example.com", "strangerbooker")
    booking = _make_booking(client, owner, total_price_cents=800)
    resp = client.post(
        f"{BOOKINGS}/{booking['id']}/cancel", headers=_auth(stranger)
    )
    assert resp.status_code == 403, resp.text


def test_pay_unknown_booking_404(client: TestClient) -> None:
    owner = _register(client, "p3@example.com", "payer3")
    resp = client.post(
        f"{BOOKINGS}/{uuid.uuid4()}/pay",
        json={"idempotency_key": "missing-key-1"},
        headers=_auth(owner),
    )
    assert resp.status_code == 404, resp.text


# ---------------------------------------------------------------------------
# Part B: payment provider abstraction (unit level, no HTTP)
# ---------------------------------------------------------------------------
def test_mock_provider_is_deterministic_and_idempotent() -> None:
    from app.services.payments import PaymentIntentStatus, get_payment_provider

    provider = get_payment_provider("mock")
    a = provider.create_payment_intent(
        amount_cents=1000, currency="EUR", idempotency_key="unit-key-1"
    )
    b = provider.create_payment_intent(
        amount_cents=1000, currency="EUR", idempotency_key="unit-key-1"
    )
    assert a.reference == b.reference  # same key -> same intent
    confirmed = provider.confirm_payment(reference=a.reference)
    assert confirmed.status == PaymentIntentStatus.SUCCEEDED

    refund = provider.refund(
        payment_reference=a.reference,
        amount_cents=1000,
        currency="EUR",
        idempotency_key="unit-refund-1",
    )
    again = provider.refund(
        payment_reference=a.reference,
        amount_cents=1000,
        currency="EUR",
        idempotency_key="unit-refund-1",
    )
    assert refund.reference == again.reference


def test_provider_factory_defaults_to_mock() -> None:
    from app.services.payments import MockProvider, get_payment_provider

    assert isinstance(get_payment_provider(), MockProvider)


def test_stripe_provider_without_keys_raises_notimplemented() -> None:
    import os

    from app.services.payments import get_payment_provider

    saved = os.environ.pop("STRIPE_SECRET_KEY", None)
    try:
        try:
            get_payment_provider("stripe")
        except NotImplementedError as exc:
            assert "Stripe provider is not configured" in str(exc)
        else:  # pragma: no cover - defensive
            raise AssertionError("expected NotImplementedError without keys")
    finally:
        if saved is not None:
            os.environ["STRIPE_SECRET_KEY"] = saved


def test_unknown_provider_name_rejected() -> None:
    import pytest

    from app.services.payments import get_payment_provider

    with pytest.raises(ValueError):
        get_payment_provider("paypal")


# ---------------------------------------------------------------------------
# Part C: payment is a REAL gate on booking confirmation
# ---------------------------------------------------------------------------
import pytest

from app.services.payments import (
    PaymentIntent,
    PaymentIntentStatus,
    PaymentProvider,
    PaymentProviderError,
    RefundResult,
    WebhookEvent,
    WebhookVerificationError,
)


class _DecliningProvider(PaymentProvider):
    """A provider whose charge is always declined (for the failure path)."""

    name = "declining"

    def create_payment_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        idempotency_key: str,
        metadata: dict | None = None,
    ) -> PaymentIntent:
        return PaymentIntent(
            provider=self.name,
            reference=f"pi_declined_{idempotency_key}",
            amount_cents=amount_cents,
            currency=currency.upper(),
            status=PaymentIntentStatus.REQUIRES_CONFIRMATION,
            idempotency_key=idempotency_key,
            metadata=dict(metadata or {}),
        )

    def confirm_payment(
        self, *, reference: str, idempotency_key: str | None = None
    ) -> PaymentIntent:
        raise PaymentProviderError("card declined")

    def refund(self, **kwargs: object) -> RefundResult:  # pragma: no cover
        raise PaymentProviderError("nothing to refund")

    def verify_webhook(self, *, payload: bytes, signature: str | None) -> WebhookEvent:
        raise WebhookVerificationError("unsupported")


def test_payment_success_confirms_booking(client: TestClient) -> None:
    """A captured payment is the thing that flips a booking to confirmed."""
    owner = _register(client, "gate1@example.com", "gatepayer1")
    booking = _make_booking(client, owner, total_price_cents=2500)
    assert booking["status"] == "pending"
    assert booking["payment_status"] == "pending"

    pay = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "gate-pay-0001"},
        headers=_auth(owner),
    )
    assert pay.status_code == 201, pay.text
    assert pay.json()["status"] == "paid"
    assert pay.json()["provider_reference"], "captured payment must carry a ref"

    after = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert after["status"] == "confirmed"
    assert after["payment_status"] == "paid"


def test_payment_failure_does_not_confirm(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A declined charge leaves the booking pending and never paid."""
    import app.services.payment_service as ps

    monkeypatch.setattr(ps, "get_default_provider", lambda: _DecliningProvider())

    owner = _register(client, "gate2@example.com", "gatepayer2")
    booking = _make_booking(client, owner, total_price_cents=3000)
    assert booking["status"] == "pending"

    pay = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "gate-fail-0002"},
        headers=_auth(owner),
    )
    assert pay.status_code == 402, pay.text
    assert "declined" in pay.json()["detail"].lower()

    after = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert after["status"] == "pending", "a failed payment must not confirm"
    assert after["payment_status"] != "paid"
    assert [p["status"] for p in after["payments"]] == ["failed"]

    bal = client.get(f"{BOOKINGS}/{booking['id']}/balance", headers=_auth(owner)).json()
    assert bal["paid_cents"] == 0
    assert bal["outstanding_cents"] == 3000


def test_payment_replay_is_idempotent(client: TestClient) -> None:
    """Replaying the same idempotency key never double-charges."""
    owner = _register(client, "gate3@example.com", "gatepayer3")
    booking = _make_booking(client, owner, total_price_cents=1800)

    first = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "gate-replay-0003"},
        headers=_auth(owner),
    )
    replay = client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "gate-replay-0003"},
        headers=_auth(owner),
    )
    assert first.status_code == 201 and replay.status_code == 201
    assert first.json()["id"] == replay.json()["id"]

    detail = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    paid = [p for p in detail["payments"] if p["status"] == "paid"]
    assert len(paid) == 1, "replay must not create a second captured payment"
    bal = client.get(f"{BOOKINGS}/{booking['id']}/balance", headers=_auth(owner)).json()
    assert bal["paid_cents"] == 1800, "replay must not double-charge"


def test_refund_sets_both_sides_consistently(client: TestClient) -> None:
    """Refunding moves payment -> REFUNDED and booking -> REFUNDED, once."""
    owner = _register(client, "gate4@example.com", "gatepayer4")
    booking = _make_booking(client, owner, total_price_cents=1400)
    client.post(
        f"{BOOKINGS}/{booking['id']}/pay",
        json={"idempotency_key": "gate-refund-0004"},
        headers=_auth(owner),
    )

    first = client.post(f"{BOOKINGS}/{booking['id']}/refund", headers=_auth(owner))
    assert first.status_code == 200, first.text
    assert len(first.json()) == 1, "one refund for the one captured payment"

    after = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert after["status"] == "refunded"
    assert after["payment_status"] == "refunded"
    assert [p["status"] for p in after["payments"]] == ["refunded"]

    # Replay: no new refund rows, no double-refund, state unchanged.
    replay = client.post(f"{BOOKINGS}/{booking['id']}/refund", headers=_auth(owner))
    assert replay.status_code == 200
    assert replay.json() == []
    still = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert still["status"] == "refunded"
    assert still["payment_status"] == "refunded"


def test_unconfirmed_booking_is_not_treated_as_paid(client: TestClient) -> None:
    """An unpaid booking is pending everywhere and cannot be paid-treated."""
    owner = _register(client, "gate5@example.com", "gatepayer5")
    booking = _make_booking(client, owner, total_price_cents=900)
    assert booking["status"] == "pending"
    assert booking["payment_status"] == "pending"

    detail = client.get(f"{BOOKINGS}/{booking['id']}", headers=_auth(owner)).json()
    assert detail["status"] == "pending"
    assert detail["payment_status"] == "pending"
    assert all(p["status"] != "paid" for p in detail["payments"])

    bal = client.get(f"{BOOKINGS}/{booking['id']}/balance", headers=_auth(owner)).json()
    assert bal["paid_cents"] == 0
    assert bal["outstanding_cents"] == 900



def test_gate_refuses_to_confirm_without_captured_payment(db_session) -> None:
    """The server-side gate itself refuses a booking that is only pending.

    A paid split with no provider-captured payment (no provider reference)
    must NOT confirm the booking - payment success is what gates it.
    """
    from datetime import UTC, datetime

    from app.models.booking import Booking, Payment, PaymentSplit
    from app.models.enums import BookingStatus, PaymentStatus, SplitStatus
    from app.models.user import User
    from app.services.payment_service import PaymentService

    user = User(
        email="gate7@example.com",
        username="gatepayer7",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.flush()

    booking = Booking(
        booked_by_id=user.id,
        total_price_cents=1000,
        currency="EUR",
        status=BookingStatus.PENDING,
        starts_at=datetime(2030, 1, 1, 10, tzinfo=UTC),
        ends_at=datetime(2030, 1, 1, 11, tzinfo=UTC),
    )
    db_session.add(booking)
    db_session.flush()
    payment = Payment(
        booking_id=booking.id,
        payer_id=user.id,
        amount_cents=1000,
        currency="EUR",
        status=PaymentStatus.PENDING,
    )
    db_session.add(payment)
    db_session.flush()
    db_session.add(
        PaymentSplit(
            payment_id=payment.id,
            booking_id=booking.id,
            user_id=user.id,
            share_cents=1000,
            currency="EUR",
            status=SplitStatus.PAID,
        )
    )
    db_session.commit()

    gate = PaymentService(db_session)
    assert gate.confirm_booking_if_settled(booking.id) is None
    db_session.refresh(booking)
    assert booking.status == BookingStatus.PENDING
