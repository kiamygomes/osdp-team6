"""Pytest fixtures & test-time environment.

This module provides common test setup helpers, fixtures, and mock builders
to reduce duplication across test files.
"""  # noqa: INP001

import os

# Set test env *before* importing anything that pulls ticket_impl.config
os.environ.setdefault("JIRA_CLOUD_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("OAUTH_CLIENT_ID", "test-client-id")
os.environ.setdefault("OAUTH_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("OAUTH_REDIRECT_URI", "http://localhost/callback")
os.environ.setdefault("DB_URL", "sqlite:///./test_tokens.db")

import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
import respx
from ticket_impl.config import settings
from ticket_impl.storage import map_uuid_to_key, upsert_tokens

# Constants
BASE_URL = f"https://api.atlassian.com/ex/jira/{settings.jira_cloud_id}/rest/api/3"
HTTP_NOT_FOUND = 404  # HTTP status code for resource not found


@dataclass
class JiraIssueData:
    """Data class for building Jira issue payloads with sensible defaults."""

    issue_id: str = "10001"
    key: str = "OSDP-101"
    summary: str = "Test Issue"
    status: str = "Open"
    priority: str = "Medium"
    description: str = "Test description"
    assignee: str | None = "Terra"
    reporter: str | None = "Terra"


@pytest.fixture
def seed_token() -> None:
    """Insert a valid token row for user u1."""
    upsert_tokens("u1", "ACCESS_TOKEN", "REFRESH_TOKEN", 3600)


@pytest.fixture
def base_url() -> str:
    """Provide the base Jira API URL for tests."""
    return BASE_URL


@pytest.fixture
def test_user_id() -> str:
    """Provide a consistent test user ID."""
    return "test-user-1"


@pytest.fixture
def test_project_key() -> str:
    """Provide a consistent test project key."""
    return "OSDP"


@pytest.fixture
def test_ticket_id() -> UUID:
    """Provide a consistent test ticket UUID."""
    return uuid4()


@pytest.fixture
def test_jira_key() -> str:
    """Provide a consistent test Jira key."""
    return "OSDP-101"


def setup_ticket_uuid_mapping(
    user_id: str,
    ticket_id: UUID,
    jira_key: str,
) -> None:
    """Map UUID to Jira key in storage.

    Args:
        user_id: The user ID for the mapping
        ticket_id: The UUID to map
        jira_key: The Jira key to map to

    Example:
        >>> ticket_id = uuid4()
        >>> setup_ticket_uuid_mapping("user1", ticket_id, "OSDP-101")

    """
    map_uuid_to_key(user_id, ticket_id, jira_key)


def mock_user_search(
    base_url: str,
    *,
    account_id: str = "acc-1",
    display_name: str = "Terra",
    empty: bool = False,
) -> None:
    """Mock Jira user search endpoint.

    Args:
        base_url: Base URL for Jira API
        account_id: Account ID to return (keyword-only)
        display_name: Display name to return (keyword-only)
        empty: If True, return empty list indicating user not found (keyword-only)

    Example:
        >>> mock_user_search(BASE_URL, account_id="acc-123", display_name="Alice")

    """
    json_response = [] if empty else [{"accountId": account_id, "displayName": display_name}]
    respx.get(re.compile(f"{re.escape(base_url)}/user/search\\?.*")).mock(
        return_value=httpx.Response(200, json=json_response),
    )


def build_jira_issue_payload(
    data: JiraIssueData | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Build a standard Jira issue JSON payload for mocking.

    Args:
        data: JiraIssueData instance with values (uses defaults if None)
        **overrides: Individual field overrides

    Returns:
        Dictionary matching Jira API response structure

    Example:
        >>> payload = build_jira_issue_payload(key="OSDP-202", summary="Bug fix")
        >>> custom_data = JiraIssueData(key="OSDP-303", priority="High")
        >>> payload = build_jira_issue_payload(custom_data)

    """
    if data is None:
        data = JiraIssueData(**overrides)
    else:
        # Apply overrides to the provided data
        for key, value in overrides.items():
            setattr(data, key, value)

    return {
        "id": data.issue_id,
        "key": data.key,
        "fields": {
            "summary": data.summary,
            "status": {"name": data.status},
            "priority": {"name": data.priority},
            "description": data.description,
            "assignee": {"displayName": data.assignee} if data.assignee else None,
            "reporter": {"displayName": data.reporter} if data.reporter else None,
        },
    }


def mock_jira_get_issue(
    base_url: str,
    key: str,
    issue_payload: dict[str, Any] | None = None,
    status_code: int = 200,
) -> None:
    """Mock GET request for a Jira issue.

    Args:
        base_url: Base URL for Jira API
        key: Jira issue key
        issue_payload: Optional custom payload (default uses build_jira_issue_payload)
        status_code: HTTP status code to return

    Example:
        >>> mock_jira_get_issue(BASE_URL, "OSDP-101")
        >>> # Or with custom payload:
        >>> payload = build_jira_issue_payload(summary="Custom")
        >>> mock_jira_get_issue(BASE_URL, "OSDP-101", issue_payload=payload)

    """
    if issue_payload is None:
        issue_payload = build_jira_issue_payload(key=key)

    if status_code == HTTP_NOT_FOUND:
        respx.get(f"{base_url}/issue/{key}").mock(
            return_value=httpx.Response(HTTP_NOT_FOUND, json={"error": "Not found"}),
        )
    else:
        respx.get(f"{base_url}/issue/{key}").mock(
            return_value=httpx.Response(status_code, json=issue_payload),
        )
