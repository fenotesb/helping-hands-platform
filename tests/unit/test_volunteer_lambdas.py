import json
import os

import boto3
from moto import mock_aws

# Import your lambda handlers
from resources.lambdas.create_volunteer_lambda.app import lambda_handler as create_volunteer
from resources.lambdas.get_volunteer_lambda.app import lambda_handler as get_volunteer
from resources.lambdas.list_volunteers_lambda.app import lambda_handler as list_volunteers

TABLE_NAME = "HelpingHands_Volunteers_Test"


def setup_dynamodb():
    dynamo = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamo.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    return table


@mock_aws
def test_create_volunteer_success(monkeypatch):
    # Arrange: env var + fake table
    monkeypatch.setenv("VOLUNTEER_TABLE", TABLE_NAME)
    setup_dynamodb()

    payload = {
        "name": "Test Volunteer",
        "email": "test.volunteer@example.com",
        "phone": "555-1234",
        "city": "Brooklyn",
        "areas_of_interest": ["youth", "community"],
        "skills": ["tutoring", "organization"],
        "availability": "Weekends",
        "preferred_contact_method": "email",
    }
    event = {"body": json.dumps(payload)}

    # Act
    resp = create_volunteer(event, None)
    assert resp["statusCode"] == 201

    body = json.loads(resp["body"])
    assert "id" in body
    volunteer_id = body["id"]
    assert volunteer_id

    # Now test that get_volunteer can retrieve it
    get_event = {"pathParameters": {"id": volunteer_id}}
    get_resp = get_volunteer(get_event, None)
    assert get_resp["statusCode"] == 200

    stored = json.loads(get_resp["body"])

    # Verify key fields persisted correctly
    assert stored["id"] == volunteer_id
    assert stored["name"] == payload["name"]
    assert stored["email"] == payload["email"]
    assert stored["city"] == payload["city"]
    assert stored["areas_of_interest"] == payload["areas_of_interest"]
    assert stored["skills"] == payload["skills"]
    assert stored["availability"] == payload["availability"]
    assert stored["preferred_contact_method"] == payload["preferred_contact_method"]
    assert stored["is_active"] is True

    # Timestamp sanity check (matches create_volunteer_lambda)
    assert "createdAt" in stored
    assert stored["createdAt"]


@mock_aws
def test_create_volunteer_validation_error(monkeypatch):
    # Arrange
    monkeypatch.setenv("VOLUNTEER_TABLE", TABLE_NAME)
    setup_dynamodb()

    # Missing name + email
    event = {"body": json.dumps({"city": "Brooklyn"})}

    # Act
    resp = create_volunteer(event, None)
    assert resp["statusCode"] == 400

    body = json.loads(resp["body"])
    assert "name and email are required" in body.get("message", "")


@mock_aws
def test_list_volunteers(monkeypatch):
    # Arrange
    monkeypatch.setenv("VOLUNTEER_TABLE", TABLE_NAME)
    table = setup_dynamodb()

    # Pre-insert a couple of volunteer records (must include "id")
    table.put_item(
        Item={
            "id": "VOL1",
            "name": "Alice",
            "email": "alice@example.com",
            "city": "Queens",
        }
    )
    table.put_item(
        Item={
            "id": "VOL2",
            "name": "Bob",
            "email": "bob@example.com",
            "city": "Brooklyn",
        }
    )

    # Act
    event = {}  # list lambda doesn't really use event
    resp = list_volunteers(event, None)
    assert resp["statusCode"] == 200

    items = json.loads(resp["body"])
    emails = {v["email"] for v in items}
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails


@mock_aws
def test_get_volunteer_not_found(monkeypatch):
    """
    If a volunteer ID doesn't exist, we should get a 404.
    """
    monkeypatch.setenv("VOLUNTEER_TABLE", TABLE_NAME)
    setup_dynamodb()

    # No items inserted on purpose
    get_event = {"pathParameters": {"id": "NON_EXISTENT"}}
    resp = get_volunteer(get_event, None)

    assert resp["statusCode"] == 404
    body = json.loads(resp["body"])
    assert "Volunteer not found" in body.get("message", "")


@mock_aws
def test_get_volunteer_missing_id(monkeypatch):
    """
    If the path parameter is missing, we should get a 400.
    """
    monkeypatch.setenv("VOLUNTEER_TABLE", TABLE_NAME)
    setup_dynamodb()

    # pathParameters is missing id
    get_event = {"pathParameters": {}}
    resp = get_volunteer(get_event, None)

    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "id is required" in body.get("message", "")
