terraform {
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "1.8.0"
    }
  }

  # Use local backend for CircleCI - state is ephemeral per workflow
  # In production, consider using remote backend (S3, Terraform Cloud, etc.)
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "render" {
  api_key = var.render_api_key
  # owner_id is optional - if not provided, uses the account associated with the API key
  owner_id = var.render_owner_id
}

# Import existing service - uncomment and add service ID to import
# Run: terraform import render_web_service.ticket_service <service-id>
# Or add this block and run terraform plan -generate-config-out=generated.tf
# import {
#   to = render_web_service.ticket_service
#   id = "<your-service-id>"
# }

resource "render_web_service" "ticket_service" {
  name   = "osdp-team6"
  plan   = var.render_plan
  region = var.render_region

  runtime_source = {
    docker = {
      repo_url        = var.repo_url
      branch          = var.repo_branch
      dockerfile_path = "Dockerfile"
      auto_deploy     = var.auto_deploy
    }
  }

  env_vars = {
    JIRA_CLOUD_ID = {
      value = var.jira_cloud_id
    }
    JIRA_API_BASE = {
      value = "https://api.atlassian.com/ex/jira/${var.jira_cloud_id}"
    }
    OAUTH_CLIENT_ID = {
      value = var.oauth_client_id
    }
    OAUTH_CLIENT_SECRET = {
      value = var.oauth_client_secret
    }
    OAUTH_REDIRECT_URI = {
      value = "https://osdp-team6.onrender.com/api/v1/auth/callback"
    }
    DB_URL = {
      value = "sqlite:///./jira_tokens.db"
    }
  }
}

output "service_url" {
  description = "URL of the deployed service"
  value       = "https://osdp-team6.onrender.com"
}