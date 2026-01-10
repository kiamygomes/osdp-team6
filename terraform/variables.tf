variable "render_api_key" {
  description = "Render API key from https://dashboard.render.com/account"
  type        = string
  sensitive   = true
  default     = null
}

variable "render_owner_id" {
  description = "Render owner/team ID from dashboard URL"
  type        = string
  default     = null
}

variable "repo_url" {
  description = "Git repository URL"
  type        = string
  default     = null
}

variable "repo_branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

variable "render_plan" {
  description = "Render plan: free, starter, standard, pro"
  type        = string
  default     = "starter"
}

variable "render_region" {
  description = "Render region: oregon, frankfurt, singapore, ohio, virginia"
  type        = string
  default     = "virginia"
}

variable "auto_deploy" {
  description = "Auto-deploy on git push"
  type        = bool
  default     = true
}

variable "jira_cloud_id" {
  description = "Jira Cloud ID"
  type        = string
  default     = null
}

variable "oauth_client_id" {
  description = "Jira OAuth Client ID"
  type        = string
  sensitive   = true
  default     = null
}

variable "oauth_client_secret" {
  description = "Jira OAuth Client Secret"
  type        = string
  sensitive   = true
  default     = null
}