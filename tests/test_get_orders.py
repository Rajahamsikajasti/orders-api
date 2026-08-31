import json
from tests.conftest import api_event


def _create_sample_order(customer_id="cust-123"):
    from handlers.create_order import lambda_handler as create_handler

    event = api_event(
        method="POST",
        path="/orders",
        body={
            "customerId": customer_id,
            "items": [{"sku": "SKU-1", "name": "Widget", "quantity": 1, "price": 5.00}],
        },
    )
    result = create_handler(event, {})
    return json.loads(result["body"])["orderId"]


def test_get_orders_by_customer_empty(dynamodb_table):
    from handlers.get_orders import lambda_handler

    event = api_event(method="GET", path="/orders/cust-999", path_params={"customerId": "cust-999"})
    result = lambda_handler(event, {})
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["count"] == 0
    assert body["orders"] == []


def test_get_orders_by_customer_returns_created_order(dynamodb_table):
    from handlers.get_orders import lambda_handler

    order_id = _create_sample_order("cust-123")

    event = api_event(method="GET", path="/orders/cust-123", path_params={"customerId": "cust-123"})
    result = lambda_handler(event, {})
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["count"] == 1
    assert body["orders"][0]["orderId"] == order_id
    assert body["orders"][0]["status"] == "PENDING"


def test_get_single_order_not_found(dynamodb_table):
    from handlers.get_orders import lambda_handler

    event = api_event(
        method="GET",
        path="/orders/cust-123/does-not-exist",
        path_params={"customerId": "cust-123", "orderId": "does-not-exist"},
    )
    result = lambda_handler(event, {})

    assert result["statusCode"] == 404


def test_get_single_order_found(dynamodb_table):
    from handlers.get_orders import lambda_handler

    order_id = _create_sample_order("cust-123")

    event = api_event(
        method="GET",
        path=f"/orders/cust-123/{order_id}",
        path_params={"customerId": "cust-123", "orderId": order_id},
    )
    result = lambda_handler(event, {})
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["orderId"] == order_id
