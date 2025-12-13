import json
import os
import base64
import urllib.request
import urllib.error


def _paypal_config():
    """
    Read PayPal config at runtime (not import-time) so unit tests can monkeypatch env vars.
    """
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_SECRET") or os.environ.get("PAYPAL_CLIENT_SECRET")
    base_url = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
    return client_id, secret, base_url


def get_access_token():
    client_id, secret, base_url = _paypal_config()

    if not client_id or not secret:
        raise EnvironmentError(
            "PAYPAL_CLIENT_ID and PAYPAL_SECRET (or PAYPAL_CLIENT_SECRET) must be set"
        )

    auth = base64.b64encode(f"{client_id}:{secret}".encode()).decode()

    req = urllib.request.Request(
        f"{base_url}/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        res = urllib.request.urlopen(req).read()
        return json.loads(res)["access_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"PayPal token request failed: {e.code} {body}") from e


def lambda_handler(event, context):
    # Parse request body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid JSON body"})}

    order_id = body.get("orderId") or body.get("id")
    if not order_id:
        return {"statusCode": 400, "body": json.dumps({"message": "orderId is required"})}

    # Get OAuth token
    try:
        access_token = get_access_token()
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}

    # Capture order
    _, _, base_url = _paypal_config()

    req = urllib.request.Request(
        f"{base_url}/v2/checkout/orders/{order_id}/capture",
        data=b"{}",  # ensure POST
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        res = json.loads(urllib.request.urlopen(req).read())
        return {"statusCode": 200, "body": json.dumps(res)}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {
            "statusCode": 502,
            "body": json.dumps({"message": f"PayPal capture failed: {e.code} {body}"}),
        }
