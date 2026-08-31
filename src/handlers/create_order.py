"""
POST /orders

Creates a new order. Expects a JSON body like:

{
    "customerId": "cust-123",
    "items": [
        {"sku": "SKU-1", "name": "Widget", "quantity": 2, "price": 9.99}
    ],
    "shippingAddress": {
        "line1": "123 Main St",
        "city": "Franklin",
        "state": "TN",
        "zip": "37064"
    }
}

Writes an item to DynamoDB with:
    PK = CUSTOMER#<customerId>
    SK = ORDER#<orderId>       (orderId is server-generated, UUID4)
    status = "PENDING"
    createdAt / updatedAt = ISO-8601 UTC timestamps

Returns 201 with the created order on success.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from common.db import get_table, customer_pk, order_sk
from common.utils import response, error_response, parse_body, require_fields, logger


def _to_decimal(value):
    """Recursively convert floats to Decimal so DynamoDB will accept them."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [_to_decimal(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_decimal(v) for k, v in value.items()}
    return value


def lambda_handler(event, context):
    try:
        payload = parse_body(event)
    except ValueError as exc:
        return error_response(400, "Invalid request body", str(exc))

    missing = require_fields(payload, ["customerId", "items"])
    if missing:
        return error_response(400, "Missing required field(s)", ", ".join(missing))

    if not isinstance(payload.get("items"), list) or len(payload["items"]) == 0:
        return error_response(400, "`items` must be a non-empty array")

    customer_id = str(payload["customerId"])
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    items = _to_decimal(payload["items"])
    total_amount = sum(
        Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 1)))
        for item in payload["items"]
    )

    order_item = {
        "PK": customer_pk(customer_id),
        "SK": order_sk(order_id),
        "OrderId": order_id,
        "CustomerId": customer_id,
        "Items": items,
        "TotalAmount": Decimal(str(total_amount)),
        "ShippingAddress": _to_decimal(payload.get("shippingAddress", {})),
        "Status": "PENDING",
        "CreatedAt": now,
        "UpdatedAt": now,
    }

    try:
        table = get_table()
        table.put_item(Item=order_item, ConditionExpression="attribute_not_exists(PK)")
    except Exception as exc:  # noqa: BLE001 - surface as 500, log details
        logger.exception("Failed to write order to DynamoDB")
        return error_response(500, "Failed to create order", str(exc))

    return response(
        201,
        {
            "orderId": order_id,
            "customerId": customer_id,
            "status": "PENDING",
            "totalAmount": float(total_amount),
            "createdAt": now,
            "updatedAt": now,
            "items": payload["items"],
            "shippingAddress": payload.get("shippingAddress", {}),
        },
    )
