"""Shared fixtures for E2E tests."""

import os
from collections.abc import Generator

import httpx
import pytest
from dotenv import load_dotenv

# Load .env file (override existing env vars)
load_dotenv(override=True)

# --- Environment configuration ---
BASE_URL = os.getenv("BASE_URL", "https://osdp-team6.onrender.com")
OAUTH_USER_ID = os.getenv("OAUTH_USER_ID", "6b289e28-8530-4e2f-a8a7-6d2ec8dbe3c2")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")


@pytest.fixture(scope="module")
def deployed_client() -> Generator[httpx.Client, None, None]:
    """Create HTTP client for the deployed Render API.

    Uses Cookie header for authentication (same as browser).
    Tokens must be refreshed by visiting: {BASE_URL}/api/v1/auth/login
    """
    # Use Cookie header for authentication (httpx cookies with base_url can be tricky)
    headers = {
        "X-Project-Key": PROJECT_KEY,
        "Cookie": f"user_id={OAUTH_USER_ID}",
    }

    client = httpx.Client(base_url=BASE_URL, headers=headers, timeout=30.0)
    yield client
    client.close()
