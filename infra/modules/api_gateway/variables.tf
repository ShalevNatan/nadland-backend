variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for JWT authorizer"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito App Client ID for JWT authorizer"
  type        = string
}

variable "lambda_calculate_name" {
  description = "Calculate Lambda function name"
  type        = string
}

variable "lambda_calculate_arn" {
  description = "Calculate Lambda function ARN"
  type        = string
}

variable "lambda_get_history_name" {
  description = "Get history Lambda function name"
  type        = string
}

variable "lambda_get_history_arn" {
  description = "Get history Lambda function ARN"
  type        = string
}

variable "lambda_health_name" {
  description = "Health Lambda function name"
  type        = string
}

variable "lambda_health_arn" {
  description = "Health Lambda function ARN"
  type        = string
}

variable "allow_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}
