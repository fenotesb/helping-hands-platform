import json
import urllib.error

import pytest

from resources.lambdas.capture_paypal_order_lambda import app as capture_app


@pytest.fixture
def paypal_env(monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("PAYPAL_SECRET", "test_secret")
    monkeypatch.setenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")


def test_capture_missing_order_id(paypal_env):
    resp = capture_app.lambda_handler({"body": json.dumps({})}, None)
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "orderId is required" in body["message"]


def test_capture_invalid_json(paypal_env):
    resp = capture_app.lambda_handler({"body": "{bad json"}, None)
    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "Invalid JSON" in body["message"]


def test_capture_success(paypal_env, monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req):
        calls["n"] += 1
        url = req.full_url

        class FakeResp:
            def __init__(self, payload):
                self._payload = payload

            def read(self):
                return json.dumps(self._payload).encode()

        # 1) token
        if url.endswith("/v1/oauth2/token"):
            return FakeResp({"access_token": "ACCESS_TOKEN"})

        # 2) capture
        if "/v2/checkout/orders/" in url and url.endswith("/capture"):
            return FakeResp({"id": "ORDER123", "status": "COMPLETED"})

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(capture_app.urllib.request, "urlopen", fake_urlopen)

    resp = capture_app.lambda_handler({"body": json.dumps({"orderId": "ORDER123"})}, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["status"] == "COMPLETED"
    assert calls["n"] == 2


def test_capture_paypal_http_error(paypal_env, monkeypatch):
    def fake_urlopen(req):
        url = req.full_url

        # token ok
        if url.endswith("/v1/oauth2/token"):
            class FakeResp:
                def read(self):
                    return b'{"access_token":"ACCESS_TOKEN"}'
            return FakeResp()

        # capture fails
        if url.endswith("/capture"):
            raise urllib.error.HTTPError(
                url=url,
                code=422,
                msg="Unprocessable Entity",
                hdrs=None,
                fp=None,
            )

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(capture_app.urllib.request, "urlopen", fake_urlopen)

    resp = capture_app.lambda_handler({"body": json.dumps({"orderId": "ORDER123"})}, None)
    assert resp["statusCode"] == 502
    body = json.loads(resp["body"])
    assert "PayPal capture failed" in body["message"]
