import json
import os
import uuid
from datetime import datetime, timezone

import boto3

dynamo = boto3.resource("dynamodb")


def get_table():
    """
    Resolve the DynamoDB table name at runtime.

    In production: VOLUNTEER_TABLE env var set by CloudFormation/SAM.
    In tests: VOLUNTEER_TABLE set by Moto fixture.
    """
    table_name = os.environ.get("VOLUNTEER_TABLE", "handsin-volunteers-dev")
    return dynamo.Table(table_name)


def lambda_handler(event, context):
    table = get_table()

    body = json.loads(event.get("body") or "{}")

    if not body.get("name") or not body.get("email"):
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "name and email are required"})
        }

    # ✅ One canonical id (matches DynamoDB partition key "id")
    volunteer_id = str(uuid.uuid4())

    item = {
        "id": volunteer_id,  # ✅ REQUIRED key for DynamoDB table
        "name": body["name"],
        "email": body["email"],
        "phone": body.get("phone"),
        "city": body.get("city"),
        "areas_of_interest": body.get("areas_of_interest", []),
        "skills": body.get("skills", []),
        "availability": body.get("availability", ""),
        "preferred_contact_method": body.get("preferred_contact_method", "email"),
        "is_active": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),  # keep camelCase consistent
    }

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "body": json.dumps({"id": volunteer_id})
    }
