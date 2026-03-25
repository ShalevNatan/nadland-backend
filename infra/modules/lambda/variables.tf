variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "function_name" {
  description = "Short name for this Lambda function"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name the function accesses"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN for IAM policy"
  type        = string
}

variable "zip_path" {
  description = "Path to the Lambda deployment zip file"
  type        = string
}
