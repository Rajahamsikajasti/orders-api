"""
GET /orders/{customerId}
GET /orders/{customerId}/{orderId}

Retrieves orders for a customer using a DynamoDB partition-key Query
(cheap and fast - no table scan). When orderId is also supplied in
the path, a single item is fetched directly via GetItem instead.

Supports optional pagination via query string parameters:
    ?limit=20&nextToken=<base64-encoded LastEvaluatedKey>

Supports optional status filtering:
    ?status=SHIPPED
"""

import base64
import json

from common.db import get_table, customer_pk, order_sk
from common.utils import response, error_response, logger


def _decode_token(token: str) -> dict:
    return json.loads(base64.b64decode(token).decode("utf-8"))


def _encode_token(key: dict) -> str:
    return base64.b64encode(json.dumps(key).encode("utf-8")).decode("utf-8")


def _format_order(item: dict) -> dict:
    return {
        "orderId": item.get("OrderId"),
        "customerId": item.get("CustomerId"),
        "status": item.get("Status"),
        "items": item.get("Items", []),
        "totalAmount": item.get("TotalAmount"),
        "shippingAddress": item.get("ShippingAddress", {}),
        "createdAt": item.get("CreatedAt"),
        "updatedAt": item.get("UpdatedAt"),
    }


def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    customer_id = path_params.get("customerId")
    order_id = path_params.get("orderId")

    if not customer_id:
        return error_response(400, "customerId path parameter is required")

    table = get_table()

    # Single order lookup: GET /orders/{customerId}/{orderId}
    if order_id:
        try:
            result = table.get_item(
                Key={"PK": customer_pk(customer_id), "SK": order_sk(order_id)}
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch order")
            return error_response(500, "Failed to fetch order", str(exc))

        item = result.get("Item")
        if not item:
            return error_response(404, "Order not found")
        return response(200, _format_order(item))

    # List orders for a customer: GET /orders/{customerId}
    query_kwargs = {
        "KeyConditionExpression": "PK = :pk",
        "ExpressionAttributeValues": {":pk": customer_pk(customer_id)},
    }

    status_filter = query_params.get("status")
    if status_filter:
        query_kwargs["FilterExpression"] = "#s = :status"
        query_kwargs["ExpressionAttributeNames"] = {"#s": "Status"}
        query_kwargs["ExpressionAttributeValues"][":status"] = status_filter.upper()

    limit = query_params.get("limit")
    if limit:
        try:
            query_kwargs["Limit"] = int(limit)
        except ValueError:
            return error_response(400, "`limit` must be an integer")

    next_token = query_params.get("nextToken")
    if next_token:
        try:
            query_kwargs["ExclusiveStartKey"] = _decode_token(next_token)
        except Exception:
            return error_response(400, "Invalid nextToken")

    try:
        result = table.query(**query_kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to query orders for customer %s", customer_id)
        return error_response(500, "Failed to fetch orders", str(exc))

    orders = [_format_order(item) for item in result.get("Items", [])]

    body = {"customerId": customer_id, "count": len(orders), "orders": orders}

    last_key = result.get("LastEvaluatedKey")
    if last_key:
        body["nextToken"] = _encode_token(last_key)

    return response(200, body)
