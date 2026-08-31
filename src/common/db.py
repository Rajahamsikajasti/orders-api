"""
DynamoDB access helpers for the Order API.

Table design (single-table):
    PK = "CUSTOMER#<customer_id>"
    SK = "ORDER#<order_id>"

A GSI named "OrderIndex" is keyed on OrderId alone, so an order can
be located even when the caller only has the OrderId (not used by
the endpoints in this project yet, but kept available for future
"get order by id" style lookups).
"""

import os
import boto3

_TABLE_NAME = os.environ.get("TABLE_NAME")
_dynamodb = boto3.resource("dynamodb")


def get_table():
    """Return the DynamoDB Table resource, lazily bound to TABLE_NAME."""
    if not _TABLE_NAME:
        raise RuntimeError("TABLE_NAME environment variable is not set")
    return _dynamodb.Table(_TABLE_NAME)


def customer_pk(customer_id: str) -> str:
    return f"CUSTOMER#{customer_id}"


def order_sk(order_id: str) -> str:
    return f"ORDER#{order_id}"
