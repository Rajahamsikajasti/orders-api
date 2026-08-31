import os
import sys
import json
import boto3
import pytest
from moto import mock_aws

# Make `src/` importable as the root for `common.*` / `handlers.*`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TABLE_NAME = "test-orders-table"


@pytest.fixture
def dynamodb_table():
    os.environ["TABLE_NAME"] = TABLE_NAME
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "OrderId", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "OrderIndex",
                    "KeySchema": [{"AttributeName": "OrderId", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        yield boto3.resource("dynamodb", region_name="us-east-1").Table(TABLE_NAME)


def api_event(method="GET", path="/orders", path_params=None, query_params=None, body=None):
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_params,
        "queryStringParameters": query_params,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body) if body is not None else None,
    }
