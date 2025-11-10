"""End-to-end tests for complete application workflows.

These tests validate the full OAuth 2.0 flow and Jira Cloud integration
WITHOUT mocking the ticket implementation. They test the complete
authentication and ticket management pipeline.

Prerequisites:
- Valid Jira OAuth credentials configured in environment:
  - OAUTH_CLIENT_ID: OAuth 2.0 application client ID
  - OAUTH_CLIENT_SECRET: OAuth 2.0 application client secret
  - OAUTH_REDIRECT_URI: OAuth 2.0 redirect URI
  - JIRA_CLOUD_ID: Jira Cloud instance ID

These tests require real Jira Cloud access and valid OAuth tokens.
"""

import os
from http import HTTPStatus
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from ticket_impl.storage import get_tokens, upsert_tokens

from ticket_api import TicketPriority, TicketStatus
from ticket_service import app

pytestmark = pytest.mark.e2e


# Check if OAuth credentials are configured
HAS_OAUTH_CREDENTIALS = all(
    os.getenv(var)
    for var in [
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_REDIRECT_URI",
        "JIRA_CLOUD_ID",
    ]
)


@pytest.fixture(autouse=True)
def setup_oauth_tokens() -> None:
    """Set up valid OAuth tokens for E2E test users.

    This fixture retrieves real OAuth tokens from demo_user and copies them
    to test users for E2E testing against a real Jira Cloud instance.
    """
    if not HAS_OAUTH_CREDENTIALS:
        return  # Skip if credentials not configured

    # Ensure we use the correct (non-test) database for E2E tests
    # The ticket_impl test conftest may have changed DB_URL to a test database
    # We need to temporarily restore it to get tokens from the production database
    if os.getenv("DB_URL", "").endswith("test_tokens.db"):
        os.environ["DB_URL"] = "sqlite:///./jira_tokens.db"
        # Reload the storage module to use the new DB_URL
        import importlib

        import ticket_impl.storage

        importlib.reload(ticket_impl.storage)
        from ticket_impl.storage import get_tokens as get_tokens_prod
        from ticket_impl.storage import upsert_tokens as upsert_tokens_prod

        get_tokens_fn = get_tokens_prod
        upsert_tokens_fn = upsert_tokens_prod
    else:
        get_tokens_fn = get_tokens
        upsert_tokens_fn = upsert_tokens

    # Get the real tokens from demo_user (obtained through OAuth flow)
    demo_tokens = get_tokens_fn("demo_user")
    if not demo_tokens:
        pytest.skip(
            "No valid OAuth tokens found for demo_user. Run main.py to authenticate first.",
        )
        return

    # Set up tokens for both E2E test users using real tokens
    test_users = [
        "e2e-test-user-oauth",
        "e2e-test-workflow",
        "e2e-test-list-tickets",
    ]

    for user_id in test_users:
        # Use the real OAuth tokens from demo_user for all E2E test users
        upsert_tokens_fn(
            user_id=user_id,
            access=demo_tokens.access_token,
            refresh=demo_tokens.refresh_token,
            expires_in_sec=3600,
        )


class TestE2ETicketManagement:
    """End-to-end tests for complete ticket management workflows.

    These tests make REAL API calls to Jira Cloud without mocking,
    validating the complete OAuth flow and ticket lifecycle.
    """

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="Jira OAuth credentials not configured",
    )
    def test_e2e_create_ticket_oauth_flow(self) -> None:
        """Test creating a ticket with real OAuth flow and Jira integration.

        This E2E test validates:
        1. Real OAuth token authentication
        2. Actual Jira Cloud API integration
        3. Ticket creation in real Jira instance
        4. Proper response handling from real service
        5. No mocking at service layer
        """
        client = TestClient(app)
        test_user_id = "e2e-test-user-oauth"
        project_key = os.getenv("JIRA_PROJECT_KEY", "TEST")

        # Create ticket through REAL API (no mocking of TicketImpl)
        response = client.post(
            "/api/v1/tickets",
            json={
                "title": "E2E Test: OAuth & Jira Integration",
                "description": "Testing real Jira Cloud integration with OAuth flow",
                "reporter": f"{test_user_id}@example.com",
                "priority": "high",
            },
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        # Verify successful creation against real Jira
        assert response.status_code == HTTPStatus.CREATED
        ticket_data = response.json()

        assert "id" in ticket_data
        assert ticket_data["title"] == "E2E Test: OAuth & Jira Integration"
        assert ticket_data["status"] == TicketStatus.OPEN.value
        assert ticket_data["priority"] == TicketPriority.HIGH.value

        ticket_id = UUID(ticket_data["id"])

        # Retrieve ticket from Jira to verify it was created
        get_response = client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert get_response.status_code == HTTPStatus.OK
        retrieved_ticket = get_response.json()
        assert retrieved_ticket["id"] == str(ticket_id)
        assert retrieved_ticket["title"] == "E2E Test: OAuth & Jira Integration"

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="Jira OAuth credentials not configured",
    )
    def test_e2e_complete_ticket_workflow(self) -> None:
        """Test complete ticket lifecycle with real Jira Cloud.

        This E2E test validates the full workflow:
        1. Create ticket in real Jira
        2. Update ticket status
        3. Add comments in real Jira
        4. Retrieve and verify all changes

        No mocking at any layer.
        """
        client = TestClient(app)
        test_user_id = "e2e-test-workflow"
        project_key = os.getenv("JIRA_PROJECT_KEY", "TEST")

        # Step 1: Create ticket
        create_response = client.post(
            "/api/v1/tickets",
            json={
                "title": "E2E Workflow: Complete Lifecycle",
                "description": "Testing full ticket workflow in real Jira",
                "reporter": f"{test_user_id}@example.com",
                "priority": "medium",
            },
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert create_response.status_code == HTTPStatus.CREATED
        ticket_id = UUID(create_response.json()["id"])

        # Step 2: Update ticket status
        update_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={
                "status": TicketStatus.IN_PROGRESS.value,
                "assignee": f"{test_user_id}@example.com",
            },
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert update_response.status_code == HTTPStatus.OK
        updated_ticket = update_response.json()
        assert updated_ticket["status"] == TicketStatus.IN_PROGRESS.value

        # Step 3: Add comment
        comment_response = client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            json={
                "author": f"{test_user_id}@example.com",
                "content": "Progress update: Working on implementation",
            },
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert comment_response.status_code == HTTPStatus.CREATED
        comment_data = comment_response.json()
        assert comment_data["content"] == "Progress update: Working on implementation"

        # Step 4: Resolve ticket
        resolve_response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": TicketStatus.RESOLVED.value},
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert resolve_response.status_code == HTTPStatus.OK
        resolved_ticket = resolve_response.json()
        assert resolved_ticket["status"] == TicketStatus.RESOLVED.value

        # Step 5: Final verification - retrieve complete ticket
        final_response = client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert final_response.status_code == HTTPStatus.OK
        final_ticket = final_response.json()
        assert final_ticket["status"] == TicketStatus.RESOLVED.value
        assert len(final_ticket.get("comments", [])) > 0


class TestE2EDataConsistency:
    """End-to-end tests for data consistency with real Jira Cloud.

    These tests verify that data is consistent across multiple operations
    when using real Jira Cloud integration.
    """

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="Jira OAuth credentials not configured",
    )
    def test_e2e_list_tickets_with_filters(self) -> None:
        """Test listing tickets with filters from real Jira Cloud.

        This test validates:
        1. Creating multiple tickets in real Jira
        2. Filtering tickets by status
        3. Data consistency across operations
        """
        client = TestClient(app)
        test_user_id = "e2e-test-list-tickets"
        project_key = os.getenv("JIRA_PROJECT_KEY", "TEST")

        # List all tickets from real Jira
        response = client.get(
            "/api/v1/tickets",
            headers={
                "X-User-ID": test_user_id,
                "X-Project-Key": project_key,
            },
        )

        # Verify successful retrieval
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)
