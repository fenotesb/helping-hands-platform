import json
import os
from datetime import datetime, timezone

import boto3

dynamo = boto3.resource("dynamodb")
table = dynamo.Table(os.environ["DONATION_TABLE"])


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    # Basic example: handle CHECKOUT.ORDER.APPROVED
    if body.get("event_type") == "CHECKOUT.ORDER.APPROVED":
        resource = body["resource"]

        donation_id = resource["id"]
        amount_info = resource["purchase_units"][0]["amount"]
        amount = amount_info["value"]
        currency = amount_info["currency_code"]

        item = {
            "donation_id": donation_id,
            "amount": amount,
            "currency": currency,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        table.put_item(Item=item)

    # You can log or handle other event types if needed

    return {"statusCode": 200, "body": "OK"}
