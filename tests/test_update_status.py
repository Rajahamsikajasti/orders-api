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


def test_update_status_success(dynamodb_table):
    from handlers.update_status import lambda_handler

    order_id = _create_sample_order("cust-123")

    event = api_event(
        method="PUT",
        path=f"/orders/cust-123/{order_id}",
        path_params={"customerId": "cust-123", "orderId": order_id},
        body={"status": "shipped"},
    )
    result = lambda_handler(event, {})
    body = json.loads(result["body"])

    assert result["statusCode"] == 200
    assert body["status"] == "SHIPPED"


def test_update_status_not_found(dynamodb_table):
    from handlers.update_status import lambda_handler

    event = api_event(
        method="PUT",
        path="/orders/cust-123/does-not-exist",
        path_params={"customerId": "cust-123", "orderId": "does-not-exist"},
        body={"status": "SHIPPED"},
    )
    result = lambda_handler(event, {})

    assert result["statusCode"] == 404


def test_update_status_invalid_value(dynamodb_table):
    from handlers.update_status import lambda_handler

    order_id = _create_sample_order("cust-123")

    event = api_event(
        method="PUT",
        path=f"/orders/cust-123/{order_id}",
        path_params={"customerId": "cust-123", "orderId": order_id},
        body={"status": "NOT_A_REAL_STATUS"},
    )
    result = lambda_handler(event, {})

    assert result["statusCode"] == 400


def test_update_status_missing_field(dynamodb_table):
    from handlers.update_status import lambda_handler

    order_id = _create_sample_order("cust-123")

    event = api_event(
        method="PUT",
        path=f"/orders/cust-123/{order_id}",
        path_params={"customerId": "cust-123", "orderId": order_id},
        body={},
    )
    result = lambda_handler(event, {})

    assert result["statusCode"] == 400
