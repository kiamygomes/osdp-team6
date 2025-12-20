"""End-to-end tests with real credentials from CircleCI.

These tests use real OAuth credentials stored in CircleCI environment variables
to test the complete application flow with actual Jira Cloud integration.

Required Environment Variables (set in CircleCI):
- OAUTH_CLIENT_ID: Jira OAuth client ID
- OAUTH_CLIENT_SECRET: Jira OAuth client secret
- OAUTH_ACCESS_TOKEN: Valid OAuth access token
- OAUTH_REFRESH_TOKEN: Valid OAuth refresh token
- JIRA_CLOUD_ID: Jira Cloud instance ID
- JIRA_PROJECT_KEY: Jira project key for testing
"""

import os
from http import HTTPStatus
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.e2e]

# Check if OAuth credentials are available
HAS_OAUTH_CREDENTIALS = all(
    os.getenv(var)
    for var in [
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_ACCESS_TOKEN",
        "OAUTH_REFRESH_TOKEN",
        "JIRA_CLOUD_ID",
    ]
)


@pytest.fixture
def oauth_user_id() -> str:
    """Get OAuth user ID from environment or use default."""
    return os.getenv("OAUTH_USER_ID", "demo_user")


@pytest.fixture
def project_key() -> str:
    """Get Jira project key from environment."""
    return os.getenv("JIRA_PROJECT_KEY", "SCRUM")


@pytest.fixture
def ticket_service_client() -> TestClient:
    """Create test client for ticket service."""
    from ticket_service import app

    return TestClient(app)


@pytest.fixture
def orchestrator_client() -> TestClient:
    """Create test client for orchestrator service."""
    from orchestrator.orchestrator_service import app

    return TestClient(app)


class TestE2ETicketServiceWithRealCredentials:
    """E2E tests for ticket service using real Jira OAuth credentials."""

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_create_ticket_with_real_oauth(
        self,
        ticket_service_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test creating a ticket with real OAuth credentials.

        This test:
        1. Uses real OAuth tokens from CircleCI environment
        2. Makes actual API calls to Jira Cloud
        3. Verifies ticket creation in real Jira instance
        """
        response = ticket_service_client.post(
            "/api/v1/tickets",
            json={
                "title": "E2E Test: Real OAuth Credentials",
                "description": "Testing with real Jira Cloud OAuth from CircleCI",
                "reporter": oauth_user_id,
                "priority": "medium",
            },
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        ticket_data = response.json()

        assert "id" in ticket_data
        assert ticket_data["title"] == "E2E Test: Real OAuth Credentials"
        assert ticket_data["status"] == "open"

        # Verify ticket exists by retrieving it
        ticket_id = UUID(ticket_data["id"])
        get_response = ticket_service_client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert get_response.status_code == HTTPStatus.OK
        retrieved_ticket = get_response.json()
        assert retrieved_ticket["id"] == str(ticket_id)

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_complete_ticket_lifecycle_real_jira(
        self,
        ticket_service_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test complete ticket lifecycle with real Jira Cloud.

        This test validates:
        1. Create ticket in real Jira
        2. Update ticket status
        3. Add comments
        4. Retrieve and verify changes
        5. All operations use real OAuth credentials
        """
        # Step 1: Create ticket
        create_response = ticket_service_client.post(
            "/api/v1/tickets",
            json={
                "title": "E2E Lifecycle Test",
                "description": "Complete workflow test with real Jira",
                "reporter": oauth_user_id,
                "priority": "high",
            },
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert create_response.status_code == HTTPStatus.CREATED
        ticket_id = UUID(create_response.json()["id"])

        # Step 2: Update ticket status
        update_response = ticket_service_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "in_progress"},
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert update_response.status_code == HTTPStatus.OK
        assert update_response.json()["status"] == "in_progress"

        # Step 3: Add comment
        comment_response = ticket_service_client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            json={
                "author": oauth_user_id,
                "content": "E2E test comment with real OAuth",
            },
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert comment_response.status_code == HTTPStatus.CREATED

        # Step 4: Verify final state
        final_response = ticket_service_client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert final_response.status_code == HTTPStatus.OK
        final_ticket = final_response.json()
        assert final_ticket["status"] == "in_progress"
        assert len(final_ticket.get("comments", [])) > 0

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_list_tickets_real_jira(
        self,
        ticket_service_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test listing tickets from real Jira Cloud."""
        response = ticket_service_client.get(
            "/api/v1/tickets",
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)


class TestE2EOrchestratorWithRealCredentials:
    """E2E tests for orchestrator service using real credentials."""

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_orchestrator_process_command_real_ai(
        self,
        orchestrator_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test orchestrator processing with real AI and Jira.

        This test validates the complete pipeline:
        1. Natural language input
        2. Real AI processing (Claude/OpenAI)
        3. Real Jira ticket creation
        4. Complete response handling
        """
        # Skip if AI credentials not available
        if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            pytest.skip("AI provider credentials not configured")

        ai_provider = "claude" if os.getenv("ANTHROPIC_API_KEY") else "openai"

        response = orchestrator_client.post(
            "/process",
            json={
                "message": "Create a ticket for E2E orchestrator testing",
                "user_id": oauth_user_id,
                "project_key": project_key,
                "ai_provider": ai_provider,
            },
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "success" in data
        assert data["ai_provider"] == ai_provider

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_orchestrator_metrics_collection(
        self,
        orchestrator_client: TestClient,
    ) -> None:
        """Test that metrics are collected during E2E operations."""
        # Make a request to generate metrics
        orchestrator_client.get("/health")

        # Check metrics endpoint
        metrics_response = orchestrator_client.get("/metrics")

        assert metrics_response.status_code == HTTPStatus.OK
        metrics_text = metrics_response.text

        # Verify metrics are present
        assert "orchestrator_requests_total" in metrics_text
        assert "orchestrator_request_duration_seconds" in metrics_text


class TestE2ETelemetryAndMonitoring:
    """E2E tests for telemetry and monitoring features."""

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_metrics_track_latency(
        self,
        ticket_service_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test that request latency is tracked in metrics."""
        # Make a request
        ticket_service_client.get(
            "/api/v1/tickets",
            headers={
                "X-User-ID": oauth_user_id,
                "X-Project-Key": project_key,
            },
        )

        # Check metrics
        metrics_response = ticket_service_client.get("/metrics")
        metrics_text = metrics_response.text

        # Verify latency metrics
        assert "http_request_duration_seconds" in metrics_text
        assert "bucket" in metrics_text  # Histogram buckets

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_metrics_track_success_rate(
        self,
        ticket_service_client: TestClient,
        oauth_user_id: str,
        project_key: str,
    ) -> None:
        """Test that success rate is tracked in metrics."""
        # Make successful request
        ticket_service_client.get(
            "/health",
        )

        # Check metrics
        metrics_response = ticket_service_client.get("/metrics")
        metrics_text = metrics_response.text

        # Verify success rate metrics
        assert "http_requests_success_total" in metrics_text

    @pytest.mark.skipif(
        not HAS_OAUTH_CREDENTIALS,
        reason="OAuth credentials not configured in CircleCI",
    )
    def test_e2e_metrics_track_failure_rate(
        self,
        ticket_service_client: TestClient,
    ) -> None:
        """Test that failure rate is tracked in metrics."""
        # Make request that will fail (no auth)
        ticket_service_client.get("/api/v1/tickets")

        # Check metrics
        metrics_response = ticket_service_client.get("/metrics")
        metrics_text = metrics_response.text

        # Verify failure rate metrics
        assert "http_requests_failure_total" in metrics_text
