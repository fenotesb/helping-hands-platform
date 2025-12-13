import json
import os
import base64
import urllib.request
import urllib.error

# Safe access: .get() so imports don't crash.
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.environ.get("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")


def normalize_amount(amount):
    if amount is None:
        raise ValueError("amount is required")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("amount must be positive")
    return round(amount, 2)


def get_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise EnvironmentError("PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET must be set")

    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()

    req = urllib.request.Request(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
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
        details = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"PayPal token request failed: {e.code} {details}")


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    raw_amount = body.get("amount", 10.0)

    try:
        amount = normalize_amount(raw_amount)
    except ValueError as e:
        return {"statusCode": 400, "body": json.dumps({"message": str(e)})}

    try:
        access_token = get_access_token()
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"message": str(e)})}

    order_body = json.dumps({
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": f"{amount:.2f}"}
        }]
    }).encode()

    req = urllib.request.Request(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        data=order_body,
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
        details = e.read().decode("utf-8", errors="replace")
        return {"statusCode": e.code, "body": json.dumps({"message": "PayPal create order failed", "details": details})}
