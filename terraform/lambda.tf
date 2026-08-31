# ---------------------------------------------------------------------------
# Lambda code packaging
#
# Mirrors template.yaml's `CodeUri: src/` - all three functions share the
# same source tree (src/common + src/handlers) and are differentiated only
# by their `handler` entry point. Terraform zips it once and reuses the
# same archive/hash for all three function resources.
# ---------------------------------------------------------------------------

data "archive_file" "lambda_src" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/build/lambda.zip"
  excludes    = ["__pycache__"]
}

# ---------------------------------------------------------------------------
# CreateOrderFunction - POST /orders
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "create_order" {
  function_name = "${var.project_name}-create-order"
  description   = "Creates a new order in DynamoDB"

  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256

  handler = "handlers.create_order.lambda_handler"
  runtime = "python3.12"
  role    = aws_iam_role.lambda_exec.arn

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TABLE_NAME              = aws_dynamodb_table.orders.name
      POWERTOOLS_SERVICE_NAME = "order-api"
      LOG_LEVEL                = var.log_level
    }
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# GetOrdersByCustomerFunction - GET /orders/{customerId} and
#                               GET /orders/{customerId}/{orderId}
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "get_orders" {
  function_name = "${var.project_name}-get-orders-by-customer"
  description   = "Retrieves orders for a given customer ID (partition-key query)"

  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256

  handler = "handlers.get_orders.lambda_handler"
  runtime = "python3.12"
  role    = aws_iam_role.lambda_exec.arn

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TABLE_NAME              = aws_dynamodb_table.orders.name
      POWERTOOLS_SERVICE_NAME = "order-api"
      LOG_LEVEL                = var.log_level
    }
  }

  tags = var.tags
}

# ---------------------------------------------------------------------------
# UpdateOrderStatusFunction - PUT /orders/{customerId}/{orderId}
# ---------------------------------------------------------------------------
resource "aws_lambda_function" "update_status" {
  function_name = "${var.project_name}-update-order-status"
  description   = "Updates the status of an existing order"

  filename         = data.archive_file.lambda_src.output_path
  source_code_hash = data.archive_file.lambda_src.output_base64sha256

  handler = "handlers.update_status.lambda_handler"
  runtime = "python3.12"
  role    = aws_iam_role.lambda_exec.arn

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TABLE_NAME              = aws_dynamodb_table.orders.name
      POWERTOOLS_SERVICE_NAME = "order-api"
      LOG_LEVEL                = var.log_level
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "create_order" {
  name              = "/aws/lambda/${aws_lambda_function.create_order.function_name}"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "get_orders" {
  name              = "/aws/lambda/${aws_lambda_function.get_orders.function_name}"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "update_status" {
  name              = "/aws/lambda/${aws_lambda_function.update_status.function_name}"
  retention_in_days = 14
  tags              = var.tags
}
