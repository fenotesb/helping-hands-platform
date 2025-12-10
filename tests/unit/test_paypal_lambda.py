import json
from types import SimpleNamespace

import pytest

from resources.lambdas.create_paypal_order_lambda import app as paypal_app


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        # Lambda handler expects bytes from urlopen().read()
        return json.dumps(self._payload).encode("utf-8")


@pytest.fixture
def fake_urlopen(monkeypatch):
    """
    Monkeypatch urllib.request.urlopen used in the create_order lambda
    so we don't hit the real PayPal API.
    """
    calls = []

    def _fake_urlopen(request, *args, **kwargs):
        # Record the request for assertions if we want
        calls.append(request)

        # Simulate a PayPal "order created" response
        payload = {
            "id": "TEST_ORDER_ID",
            "status": "CREATED",
            "links": [],
        }
        return FakeResponse(payload)

    monkeypatch.setattr(paypal_app.urllib.request, "urlopen", _fake_urlopen)
    return calls


def test_create_order_lambda_success(monkeypatch, fake_urlopen):
    """
    Validate that lambda_handler:
    - Normalizes the amount
    - Calls urlopen once for order creation
    - Returns a 200 with an id and status
    """
    # Avoid real get_access_token logic
    monkeypatch.setattr(paypal_app, "get_access_token", lambda: "FAKE_TOKEN")

    event = {
        "body": json.dumps({
            "amount": 12.345,  # will be rounded to 12.35 internally
        })
    }

    resp = paypal_app.lambda_handler(event, None)
    assert resp["statusCode"] == 200

    body = json.loads(resp["body"])
    assert body["id"] == "TEST_ORDER_ID"
    assert body["status"] == "CREATED"

    # Ensure we actually called urlopen once (for the order)
    assert len(fake_urlopen) == 1


@pytest.mark.parametrize("bad_amount", [0, -5, None])
def test_create_order_lambda_invalid_amount(monkeypatch, bad_amount):
    """
    If the amount is invalid, lambda_handler should:
    - Not call PayPal
    - Return 400 with a helpful message
    """
    # If this is accidentally called, test will fail
    monkeypatch.setattr(
        paypal_app,
        "get_access_token",
        lambda: (_ for _ in ()).throw(AssertionError("get_access_token should not be called")),
    )

    event = {"body": json.dumps({"amount": bad_amount})}

    resp = paypal_app.lambda_handler(event, None)
    assert resp["statusCode"] == 400

    body = json.loads(resp["body"])
    assert "amount" in body.get("message", "").lower()
