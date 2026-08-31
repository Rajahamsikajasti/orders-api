"""
Shared utilities: HTTP response helpers, JSON encoding for Decimal
types returned by DynamoDB, and small validation helpers.
"""

import json
import logging
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Order status values accepted by the update-status endpoint.
VALID_STATUSES = {
    "PENDING",
    "CONFIRMED",
    "PROCESSING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
}

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
}


class DecimalEncoder(json.JSONEncoder):
    """DynamoDB returns numeric types as Decimal; make them JSON-safe."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            # Whole numbers -> int, everything else -> float
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def response(status_code: int, body: dict) -> dict:
    """Build an API Gateway proxy-integration response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            **_CORS_HEADERS,
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def error_response(status_code: int, message: str, details: str | None = None) -> dict:
    body = {"error": message}
    if details:
        body["details"] = details
    logger.warning("Returning error response %s: %s (%s)", status_code, message, details)
    return response(status_code, body)


def parse_body(event: dict) -> dict:
    """Parse and return the JSON request body from an API Gateway event."""
    raw = event.get("body") or "{}"
    try:
        return json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Request body is not valid JSON: {exc}") from exc


def require_fields(payload: dict, fields: list) -> list:
    """Return the list of required field names missing from payload."""
    return [f for f in fields if not payload.get(f)]
