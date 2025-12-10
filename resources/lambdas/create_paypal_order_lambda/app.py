import json
import os
import base64
import urllib.request

# Safe access: .get() so imports don't crash.
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET")


def normalize_amount(amount):
    """
    Small helper to validate and normalize the donation amount.
    Used in both the Lambda and unit tests.
    """
    if amount is None:
        raise ValueError("amount is required")
    amount = float(amount)
    if amount <= 0:
        raise ValueError("amount must be positive")
    # Round to 2 decimal places
    return round(amount, 2)


def get_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_SECRET:
        # In real AWS, we'd rather fail loudly here than at import time.
        raise EnvironmentError("PAYPAL_CLIENT_ID and PAYPAL_SECRET must be set")

    auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()

    req = urllib.request.Request(
        "https://api-m.paypal.com/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    res = urllib.request.urlopen(req).read()
    return json.loads(res)["access_token"]


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    raw_amount = body.get("amount", 10.0)

    try:
        amount = normalize_amount(raw_amount)
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": str(e)}),
        }

    access_token = get_access_token()

    order_body = json.dumps({
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": f"{amount:.2f}",
            }
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api-m.paypal.com/v2/checkout/orders",
        data=order_body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

    res = json.loads(urllib.request.urlopen(req).read())

    return {
        "statusCode": 200,
        "body": json.dumps(res),
    }
