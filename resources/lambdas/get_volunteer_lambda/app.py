import json
import os
import boto3

dynamo = boto3.resource("dynamodb")


def get_table():
    table_name = os.environ.get("VOLUNTEER_TABLE", "handsin-volunteers-dev")
    return dynamo.Table(table_name)


def lambda_handler(event, context):
    table = get_table()

    params = event.get("pathParameters") or {}
    volunteer_id = params.get("id") or params.get("volunteer_id")  # support both

    if not volunteer_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "id is required"})
        }

    resp = table.get_item(Key={"id": volunteer_id})
    item = resp.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Volunteer not found"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps(item)
    }
