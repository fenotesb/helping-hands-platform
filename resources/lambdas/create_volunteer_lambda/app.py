import json
import os
import uuid
from datetime import datetime, timezone

import boto3

dynamo = boto3.resource("dynamodb")


def get_table():
    """
    Resolve the DynamoDB table name at runtime.

    In production: VOLUNTEER_TABLE env var set to real table name.
    In tests: VOLUNTEER_TABLE is set to a Moto table name.
    """
    table_name = os.environ.get("VOLUNTEER_TABLE", "HelpingHands_Volunteers")
    return dynamo.Table(table_name)


def lambda_handler(event, context):
    table = get_table()

    body = json.loads(event.get("body") or "{}")

    if not body.get("name") or not body.get("email"):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "name and email are required"})
        }

    volunteer_id = str(uuid.uuid4())
    item = {
        "volunteer_id": volunteer_id,
        "name": body["name"],
        "email": body["email"],
        "phone": body.get("phone"),
        "city": body.get("city"),
        "areas_of_interest": body.get("areas_of_interest", []),
        "skills": body.get("skills", []),
        "availability": body.get("availability", ""),
        "preferred_contact_method": body.get("preferred_contact_method", "email"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "body": json.dumps({"volunteer_id": volunteer_id})
    }
