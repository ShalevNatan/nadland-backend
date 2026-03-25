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
