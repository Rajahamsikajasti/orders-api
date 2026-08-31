"""
PUT /orders/{customerId}/{orderId}

Updates the status of an existing order. Expects a JSON body like:

    {"status": "SHIPPED"}

Uses a conditional UpdateItem so the call fails cleanly with 404 if
the order doesn't exist, rather than silently creating a new item.
"""

from datetime import datetime, timezone

from botocore.exceptions import ClientError

from common.db import get_table, customer_pk, order_sk
from common.utils import response, error_response, parse_body, VALID_STATUSES, logger


def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    customer_id = path_params.get("customerId")
    order_id = path_params.get("orderId")

    if not customer_id or not order_id:
        return error_response(400, "customerId and orderId path parameters are required")

    try:
        payload = parse_body(event)
    except ValueError as exc:
        return error_response(400, "Invalid request body", str(exc))

    new_status = str(payload.get("status", "")).upper().strip()
    if not new_status:
        return error_response(400, "Missing required field: status")

    if new_status not in VALID_STATUSES:
        return error_response(
            400,
            "Invalid status value",
            f"Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    now = datetime.now(timezone.utc).isoformat()
    table = get_table()

    try:
        result = table.update_item(
            Key={"PK": customer_pk(customer_id), "SK": order_sk(order_id)},
            UpdateExpression="SET #s = :status, UpdatedAt = :now",
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={":status": new_status, ":now": now},
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error_response(404, "Order not found")
        logger.exception("Failed to update order status")
        return error_response(500, "Failed to update order status", str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error updating order status")
        return error_response(500, "Failed to update order status", str(exc))

    updated = result["Attributes"]
    return response(
        200,
        {
            "orderId": updated.get("OrderId"),
            "customerId": updated.get("CustomerId"),
            "status": updated.get("Status"),
            "updatedAt": updated.get("UpdatedAt"),
        },
    )
