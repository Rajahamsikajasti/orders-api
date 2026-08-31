variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix applied to all resources (Lambda functions, table, API)"
  type        = string
  default     = "order-api"
}

variable "stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "dev"
}

variable "log_level" {
  description = "Log level passed to the Lambda functions"
  type        = string
  default     = "INFO"
}

variable "lambda_memory_size" {
  description = "Memory (MB) allocated to each Lambda function"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Timeout (seconds) for each Lambda function"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "order-api"
    ManagedBy = "terraform"
  }
}
