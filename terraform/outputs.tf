output "api_url" {
  description = "Base URL for the Order API"
  value       = "https://${aws_api_gateway_rest_api.order_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.order_api.stage_name}"
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB orders table"
  value       = aws_dynamodb_table.orders.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB orders table"
  value       = aws_dynamodb_table.orders.arn
}

output "create_order_function_arn" {
  value = aws_lambda_function.create_order.arn
}

output "get_orders_function_arn" {
  value = aws_lambda_function.get_orders.arn
}

output "update_status_function_arn" {
  value = aws_lambda_function.update_status.arn
}
