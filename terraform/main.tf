/**
 * Main Terraform Configuration for Ticket Bot Application
 *
 * This infrastructure provisions:
 * - Container registry for Docker images
 * - Cloud Run service for the ticket bot application
 * - Environment variables and secrets management
 * - IAM permissions for service account
 */

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a service account for the application
resource "google_service_account" "ticket_bot" {
  account_id   = "ticket-bot-sa"
  display_name = "Ticket Bot Service Account"
  description  = "Service account for the Ticket Bot application"
}

# Cloud Run service for the main ticket bot application
resource "google_cloud_run_v2_service" "ticket_bot" {
  name     = "ticket-bot-orchestrator"
  location = var.region

  template {
    service_account = google_service_account.ticket_bot.email

    containers {
      image = var.container_image

      # Environment variables (non-sensitive)
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "PROJECT_KEY"
        value = var.jira_project_key
      }

      env {
        name  = "AI_PROVIDER"
        value = var.ai_provider
      }

      # Secrets from Secret Manager
      env {
        name = "JIRA_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jira_client_id.id
            version = "latest"
          }
        }
      }

      env {
        name = "JIRA_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jira_client_secret.id
            version = "latest"
          }
        }
      }

      env {
        name = "CLAUDE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.claude_api_key.id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.id
            version = "latest"
          }
        }
      }

      # Resource limits
      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
      }

      # Health check port
      ports {
        container_port = 8080
      }
    }

    # Scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Secret Manager secrets for sensitive configuration
resource "google_secret_manager_secret" "jira_client_id" {
  secret_id = "jira-client-id"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "jira_client_secret" {
  secret_id = "jira-client-secret"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "claude_api_key" {
  secret_id = "claude-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"

  replication {
    auto {}
  }
}

# IAM binding to allow service account to access secrets
resource "google_secret_manager_secret_iam_member" "jira_client_id_access" {
  secret_id = google_secret_manager_secret.jira_client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ticket_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "jira_client_secret_access" {
  secret_id = google_secret_manager_secret.jira_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ticket_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "claude_api_key_access" {
  secret_id = google_secret_manager_secret.claude_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ticket_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ticket_bot.email}"
}

# Allow unauthenticated access (can be restricted in production)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count = var.allow_public_access ? 1 : 0

  location = google_cloud_run_v2_service.ticket_bot.location
  name     = google_cloud_run_v2_service.ticket_bot.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.ticket_bot.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.ticket_bot.name
}
