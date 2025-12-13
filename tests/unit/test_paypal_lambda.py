import json
import importlib
import os
import urllib.error

import pytest


class FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


@pytest.fixture
def set_paypal_env(monkeypatch):
    """
    Set BOTH secret env var names so tests pass regardless of whether
    the Lambda uses PAYPAL_SECRET or PAYPAL_CLIENT_SECRET.
    """
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("PAYPAL_SECRET", "test-secret")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "test-secret")  # safe redundancy

    # If your code supports a base URL, set it too (harmless if unused)
    monkeypatch.setenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    yield


@pytest.fixture
def paypal_app(set_paypal_env):
    """
    Import AFTER env vars are set because your module reads env vars at import time.
    """
    mod = importlib.import_module("resources.lambdas.create_paypal_order_lambda.app")
    importlib.reload(mod)
    return mod


def test_create_order_lambda_success(paypal_app, monkeypatch):
    """
    Success path:
    - token call returns access_token
    - order call returns order json
    Works even if your code uses sandbox or prod base URLs.
    """
    def fake_urlopen(req):
        url = getattr(req, "full_url", str(req))

        if "/v1/oauth2/token" in url:
            return FakeHTTPResponse({"access_token": "FAKE_TOKEN"})

        if "/v2/checkout/orders" in url:
            return FakeHTTPResponse({"id": "ORDER123", "status": "CREATED"})

        raise AssertionError(f"Unexpected URL called: {url}")

    monkeypatch.setattr(paypal_app.urllib.request, "urlopen", fake_urlopen)

    event = {"body": json.dumps({"amount": 10.0})}
    resp = paypal_app.lambda_handler(event, None)

    # If this fails, print the body to see why
    assert resp["statusCode"] == 200, f"Expected 200, got {resp['statusCode']} body={resp.get('body')}"
    body = json.loads(resp["body"])
    assert body["id"] == "ORDER123"
    assert body["status"] == "CREATED"


@pytest.mark.parametrize("bad_amount", [0, -5, None])
def test_create_order_lambda_invalid_amount(paypal_app, bad_amount):
    event = {"body": json.dumps({"amount": bad_amount})}
    resp = paypal_app.lambda_handler(event, None)

    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "message" in body


def test_create_order_paypal_http_error_returns_failure_response(paypal_app, monkeypatch):
    """
    Simulate PayPal token endpoint returning a 401.
    Your Lambda should NOT crash tests — it should return a non-200 response.
    (If your code currently returns 500, this test allows that.)
    """

    class FakeError(urllib.error.HTTPError):
        def __init__(self):
            super().__init__(
                url="https://api-m.paypal.com/v1/oauth2/token",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            )

        def read(self):
            return b'{"error":"invalid_client"}'

    def fake_urlopen(req):
        url = getattr(req, "full_url", str(req))
        if "/v1/oauth2/token" in url:
            raise FakeError()
        raise AssertionError(f"Unexpected URL called: {url}")

    monkeypatch.setattr(paypal_app.urllib.request, "urlopen", fake_urlopen)

    event = {"body": json.dumps({"amount": 10.0})}
    resp = paypal_app.lambda_handler(event, None)

    # Accept typical behaviors:
    # - your code might return 401 (pass-through)
    # - or return 500 (wrapped/internal error)
    assert resp["statusCode"] in (401, 500), f"Got {resp['statusCode']} body={resp.get('body')}"
