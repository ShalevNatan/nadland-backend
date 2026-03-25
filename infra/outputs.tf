output "aws_region" {
  description = "AWS region in use"
  value       = var.aws_region
}

output "environment" {
  description = "Active environment"
  value       = var.environment
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = module.dynamodb.table_arn
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = module.cognito.client_id
}

output "lambda_calculate_name" {
  value = module.lambda_calculate.function_name
}

output "lambda_get_history_name" {
  value = module.lambda_get_history.function_name
}

output "lambda_health_name" {
  value = module.lambda_health.function_name
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}
