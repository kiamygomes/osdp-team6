terraform {
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "1.8.0"
    }
  }
}

provider "render" {
  api_key  = var.render_api_key
  owner_id = var.render_owner_id
}

resource "render_web_service" "ticket_service" {
  name        = "ticket-service"
  plan        = var.render_plan
  region      = var.render_region
  runtime     = "docker"
  auto_deploy = var.auto_deploy

  runtime_source = {
    native_runtime = {
      auto_deploy     = var.auto_deploy
      branch          = var.repo_branch
      repo_url        = var.repo_url
      runtime         = "docker"
      dockerfile_path = "Dockerfile"
    }
  }

  env_vars = {
    # Jira Configuration
    JIRA_CLOUD_ID       = var.jira_cloud_id
    JIRA_API_BASE       = "https://api.atlassian.com/ex/jira/${var.jira_cloud_id}"
    OAUTH_CLIENT_ID     = var.oauth_client_id
    OAUTH_CLIENT_SECRET = var.oauth_client_secret
    OAUTH_REDIRECT_URI  = "https://ticket-service.onrender.com/api/v1/auth/callback"
    
    # Database - SQLite (simple file-based)
    DB_URL = "sqlite:///./jira_tokens.db"
  }
}

output "service_url" {
  description = "URL of the deployed service"
  value       = "https://${render_web_service.ticket_service.name}.onrender.com"
}