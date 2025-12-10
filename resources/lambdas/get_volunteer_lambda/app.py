import json
import os

import boto3

dynamo = boto3.resource("dynamodb")


def get_table():
    table_name = os.environ.get("VOLUNTEER_TABLE", "HelpingHands_Volunteers")
    return dynamo.Table(table_name)


def lambda_handler(event, context):
    table = get_table()

    path_params = event.get("pathParameters") or {}
    volunteer_id = path_params.get("volunteer_id")

    if not volunteer_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "volunteer_id is required in path"})
        }

    resp = table.get_item(Key={"volunteer_id": volunteer_id})
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
