# ---------------------------------------------------------------------------
# API Gateway REST API
#
# Routes (same shape as template.yaml):
#   POST /orders
#   GET  /orders/{customerId}
#   GET  /orders/{customerId}/{orderId}
#   PUT  /orders/{customerId}/{orderId}
# ---------------------------------------------------------------------------

resource "aws_api_gateway_rest_api" "order_api" {
  name        = "${var.project_name}-api"
  description = "Serverless e-commerce Order API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# ---- /orders ---------------------------------------------------------------

resource "aws_api_gateway_resource" "orders" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id
  parent_id   = aws_api_gateway_rest_api.order_api.root_resource_id
  path_part   = "orders"
}

resource "aws_api_gateway_method" "post_orders" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.orders.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_orders" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.orders.id
  http_method             = aws_api_gateway_method.post_orders.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.create_order.invoke_arn
}

# ---- /orders/{customerId} ---------------------------------------------------

resource "aws_api_gateway_resource" "customer_id" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id
  parent_id   = aws_api_gateway_resource.orders.id
  path_part   = "{customerId}"
}

resource "aws_api_gateway_method" "get_orders_by_customer" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.customerId" = true
  }
}

resource "aws_api_gateway_integration" "get_orders_by_customer" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.customer_id.id
  http_method             = aws_api_gateway_method.get_orders_by_customer.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_orders.invoke_arn
}

# ---- /orders/{customerId}/{orderId} -----------------------------------------

resource "aws_api_gateway_resource" "order_id" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id
  parent_id   = aws_api_gateway_resource.customer_id.id
  path_part   = "{orderId}"
}

resource "aws_api_gateway_method" "get_single_order" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.order_id.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.customerId" = true
    "method.request.path.orderId"    = true
  }
}

resource "aws_api_gateway_integration" "get_single_order" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.order_id.id
  http_method             = aws_api_gateway_method.get_single_order.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_orders.invoke_arn
}

resource "aws_api_gateway_method" "update_order_status" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.order_id.id
  http_method   = "PUT"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.customerId" = true
    "method.request.path.orderId"    = true
  }
}

resource "aws_api_gateway_integration" "update_order_status" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.order_id.id
  http_method             = aws_api_gateway_method.update_order_status.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.update_status.invoke_arn
}

# ---- Lambda permissions (allow API Gateway to invoke each function) --------

resource "aws_lambda_permission" "create_order_invoke" {
  statement_id  = "AllowAPIGatewayInvokeCreateOrder"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_order.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.order_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_orders_invoke" {
  statement_id  = "AllowAPIGatewayInvokeGetOrders"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_orders.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.order_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "update_status_invoke" {
  statement_id  = "AllowAPIGatewayInvokeUpdateStatus"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.order_api.execution_arn}/*/*"
}

# ---- Deployment + stage ------------------------------------------------------

resource "aws_api_gateway_deployment" "order_api" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id

  # Forces a new deployment whenever any method/integration changes.
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.orders.id,
      aws_api_gateway_resource.customer_id.id,
      aws_api_gateway_resource.order_id.id,
      aws_api_gateway_method.post_orders.id,
      aws_api_gateway_method.get_orders_by_customer.id,
      aws_api_gateway_method.get_single_order.id,
      aws_api_gateway_method.update_order_status.id,
      aws_api_gateway_integration.post_orders.id,
      aws_api_gateway_integration.get_orders_by_customer.id,
      aws_api_gateway_integration.get_single_order.id,
      aws_api_gateway_integration.update_order_status.id,
      aws_api_gateway_method.options_orders.id,
      aws_api_gateway_method.options_customer_id.id,
      aws_api_gateway_method.options_order_id.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "order_api" {
  deployment_id = aws_api_gateway_deployment.order_api.id
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  stage_name    = var.stage_name

  xray_tracing_enabled = true
  tags                 = var.tags
}
