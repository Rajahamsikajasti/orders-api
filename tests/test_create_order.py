import json
from tests.conftest import api_event


def test_create_order_success(dynamodb_table):
    from handlers.create_order import lambda_handler

    event = api_event(
        method="POST",
        path="/orders",
        body={
            "customerId": "cust-123",
            "items": [{"sku": "SKU-1", "name": "Widget", "quantity": 2, "price": 9.99}],
            "shippingAddress": {"city": "Franklin", "state": "TN"},
        },
    )

    result = lambda_handler(event, {})
    body = json.loads(result["body"])

    assert result["statusCode"] == 201
    assert body["customerId"] == "cust-123"
    assert body["status"] == "PENDING"
    assert body["totalAmount"] == 19.98
    assert "orderId" in body


def test_create_order_missing_fields(dynamodb_table):
    from handlers.create_order import lambda_handler

    event = api_event(method="POST", path="/orders", body={"customerId": "cust-123"})
    result = lambda_handler(event, {})

    assert result["statusCode"] == 400
    assert "items" in json.loads(result["body"])["details"]


def test_create_order_invalid_json_body(dynamodb_table):
    from handlers.create_order import lambda_handler

    event = api_event(method="POST", path="/orders")
    event["body"] = "{not-valid-json"
    result = lambda_handler(event, {})

    assert result["statusCode"] == 400
