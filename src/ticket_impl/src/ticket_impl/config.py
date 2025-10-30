"""Runtime settings for Jira Cloud + OAuth."""

import os

from pydantic import BaseModel


class Settings(BaseModel):
    """Container for environment-based configuration."""

    # Jira Cloud - Use .get() with defaults instead of direct access
    jira_cloud_id: str = os.environ.get("JIRA_CLOUD_ID", "dummy-cloud-id-for-development")
    jira_api_base: str = os.environ.get(
        "JIRA_API_BASE",
        f"https://api.atlassian.com/ex/jira/{os.environ.get('JIRA_CLOUD_ID', 'dummy-cloud-id-for-development')}",
    )

    # Atlassian OAuth 2.0 (3LO) - Use .get() with defaults
    oauth_client_id: str = os.environ.get("OAUTH_CLIENT_ID", "dummy-client-id")
    oauth_client_secret: str = os.environ.get("OAUTH_CLIENT_SECRET", "dummy-client-secret")
    oauth_redirect_uri: str = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")

    # Token & mapping DB
    db_url: str = os.environ.get("DB_URL", "sqlite:///./jira_tokens.db")


settings = Settings()
