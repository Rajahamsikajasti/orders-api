# ---------------------------------------------------------------------------
# DynamoDB table
#
# Same key design as the SAM version:
#   PK (hash key)  = "CUSTOMER#<customer_id>"
#   SK (range key) = "ORDER#<order_id>"
#
# "Get all orders for a customer" is therefore a single, cheap Query
# against the partition key. The OrderIndex GSI inverts the keys so an
# order can also be found by OrderId alone.
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "orders" {
  name         = "${var.project_name}-orders-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "OrderId"
    type = "S"
  }

  global_secondary_index {
    name            = "OrderIndex"
    hash_key        = "OrderId"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = var.tags
}
