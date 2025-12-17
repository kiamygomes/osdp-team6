/**
 * Terraform Variables for Ticket Bot Infrastructure
 *
 * Define all configurable parameters for the infrastructure.
 * Values can be provided via terraform.tfvars or environment variables.
 */

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "container_image" {
  description = "Container image URL (e.g., gcr.io/PROJECT_ID/ticket-bot:latest)"
  type        = string
}

variable "jira_project_key" {
  description = "Default Jira project key"
  type        = string
  default     = "OSDP"
}

variable "ai_provider" {
  description = "AI provider to use (claude or openai)"
  type        = string
  default     = "claude"

  validation {
    condition     = contains(["claude", "openai"], var.ai_provider)
    error_message = "AI provider must be either 'claude' or 'openai'."
  }
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "allow_public_access" {
  description = "Allow unauthenticated public access to the service"
  type        = bool
  default     = false
}
