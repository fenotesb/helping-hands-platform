import json
import os

import boto3

dynamo = boto3.resource("dynamodb")


def get_table():
    table_name = os.environ.get("VOLUNTEER_TABLE", "HelpingHands_Volunteers")
    return dynamo.Table(table_name)


def lambda_handler(event, context):
    table = get_table()

    resp = table.scan()
    items = resp.get("Items", [])

    return {
        "statusCode": 200,
        "body": json.dumps(items)
    }
