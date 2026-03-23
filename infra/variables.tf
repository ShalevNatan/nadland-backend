variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (staging or prod)"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "Environment must be staging or prod."
  }
}

variable "app_name" {
  description = "Application name used for resource naming"
  type        = string
  default     = "nadland"
}

variable "alert_email" {
  description = "Email address for billing and CloudWatch alerts"
  type        = string
}
