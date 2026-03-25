provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "nadland"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

resource "aws_budgets_budget" "monthly" {
  name         = "nadland-monthly-budget"
  budget_type  = "COST"
  limit_amount = "10"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

module "dynamodb" {
  source      = "./modules/dynamodb"
  app_name    = var.app_name
  environment = var.environment
}

module "cognito" {
  source      = "./modules/cognito"
  app_name    = var.app_name
  environment = var.environment
}

data "aws_caller_identity" "current" {}

module "lambda_calculate" {
  source              = "./modules/lambda"
  app_name            = var.app_name
  environment         = var.environment
  function_name       = "calculate"
  aws_region          = var.aws_region
  account_id          = data.aws_caller_identity.current.account_id
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  zip_path            = "${path.module}/lambda_calculate.zip"
}

module "lambda_get_history" {
  source              = "./modules/lambda"
  app_name            = var.app_name
  environment         = var.environment
  function_name       = "get-history"
  aws_region          = var.aws_region
  account_id          = data.aws_caller_identity.current.account_id
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  zip_path            = "${path.module}/lambda_get_history.zip"
}

module "lambda_health" {
  source              = "./modules/lambda"
  app_name            = var.app_name
  environment         = var.environment
  function_name       = "health"
  aws_region          = var.aws_region
  account_id          = data.aws_caller_identity.current.account_id
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn
  zip_path            = "${path.module}/lambda_health.zip"
}
