"""Integration tests for Orchestrator service with AI and Ticket components.

These tests verify the interaction between:
- Orchestrator service
- AI adapter (OpenAI/Claude)
- Ticket service
"""

from datetime import UTC
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture
def orchestrator_client() -> TestClient:
    """Create test client for orchestrator service."""
    from orchestrator.orchestrator_service import app

    return TestClient(app)


@pytest.fixture
def mock_ai_response() -> dict[str, str | dict[str, str]]:
    """Mock AI response for ticket creation."""
    return {
        "action": "create_ticket",
        "parameters": {
            "title": "Fix login bug",
            "description": "Users cannot login on mobile",
            "priority": "high",
        },
    }


class TestOrchestratorAIIntegration:
    """Test integration between Orchestrator and AI components."""

    @patch("orchestrator.main_app.TicketBotOrchestrator.process_chat_message")
    def test_orchestrator_processes_command_with_ai(
        self,
        mock_process: MagicMock,
        orchestrator_client: TestClient,
    ) -> None:
        """Test that orchestrator correctly processes commands through AI."""
        # Mock successful AI processing
        mock_process.return_value = {
            "success": True,
            "message": "Ticket created successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Fix login bug",
                "status": "open",
            },
        }

        response = orchestrator_client.post(
            "/process",
            json={
                "message": "Create a ticket for fixing the login bug",
                "user_id": "test-user",
                "project_key": "TEST",
                "ai_provider": "claude",
            },
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["success"] is True
        assert data["ai_provider"] == "claude"
        assert "Ticket created" in data["message"]

    @patch("orchestrator.main_app.TicketBotOrchestrator.process_chat_message")
    def test_orchestrator_handles_ai_errors(
        self,
        mock_process: MagicMock,
        orchestrator_client: TestClient,
    ) -> None:
        """Test that orchestrator handles AI processing errors gracefully."""
        # Mock AI error
        mock_process.return_value = {
            "success": False,
            "message": "Failed to process command",
            "error": "AI service unavailable",
        }

        response = orchestrator_client.post(
            "/process",
            json={
                "message": "Invalid command",
                "user_id": "test-user",
                "project_key": "TEST",
                "ai_provider": "openai",
            },
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["success"] is False
        assert "error" in data


class TestOrchestratorTicketIntegration:
    """Test integration between Orchestrator and Ticket service."""

    @patch("ticket_impl.impl.TicketImpl.create_ticket")
    def test_orchestrator_creates_ticket_via_service(
        self,
        mock_create: AsyncMock,
        orchestrator_client: TestClient,
    ) -> None:
        """Test that orchestrator creates tickets through ticket service."""
        from datetime import datetime
        from uuid import UUID

        from ticket_api import Ticket, TicketPriority, TicketStatus

        # Mock ticket creation
        mock_ticket = Ticket(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="Integration test ticket",
            description="Test description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test-user",
            assignee=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            comments=[],
        )
        mock_create.return_value = mock_ticket

        # Mock the orchestrator's process method to return success
        with patch("orchestrator.main_app.TicketBotOrchestrator.process_chat_message") as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Ticket created successfully",
                "data": mock_ticket,
            }

            response = orchestrator_client.post(
                "/process",
                json={
                    "message": "Create a high priority ticket",
                    "user_id": "test-user",
                    "project_key": "TEST",
                    "ai_provider": "claude",
                },
            )

            assert response.status_code == HTTPStatus.OK
            data = response.json()
            assert data["success"] is True


class TestMultiComponentWorkflow:
    """Test complete workflows involving multiple components."""

    @patch("ticket_impl.impl.TicketImpl.create_ticket")
    @patch("ticket_impl.impl.TicketImpl.list_tickets")
    def test_create_and_list_workflow(
        self,
        mock_list: AsyncMock,
        mock_create: AsyncMock,
        orchestrator_client: TestClient,
    ) -> None:
        """Test creating a ticket and then listing tickets."""
        from datetime import datetime
        from uuid import UUID

        from ticket_api import Ticket, TicketPriority, TicketStatus

        # Mock ticket creation
        created_ticket = Ticket(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="Workflow test ticket",
            description="Test",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user",
            assignee=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            comments=[],
        )
        mock_create.return_value = created_ticket

        # Create ticket
        create_response = orchestrator_client.post(
            "/process",
            json={
                "message": "Create a ticket for workflow testing",
                "user_id": "test-user",
                "project_key": "TEST",
                "ai_provider": "claude",
            },
        )

        assert create_response.status_code == HTTPStatus.OK

        # Mock list tickets
        mock_list.return_value = [created_ticket]

        # List tickets
        list_response = orchestrator_client.post(
            "/process",
            json={
                "message": "List all tickets",
                "user_id": "test-user",
                "project_key": "TEST",
                "ai_provider": "claude",
            },
        )

        assert list_response.status_code == HTTPStatus.OK


class TestTelemetryIntegration:
    """Test that telemetry metrics are properly collected."""

    def test_metrics_endpoint_available(self, orchestrator_client: TestClient) -> None:
        """Test that metrics endpoint is accessible."""
        response = orchestrator_client.get("/metrics")

        assert response.status_code == HTTPStatus.OK
        assert "text/plain" in response.headers["content-type"]

    @patch("orchestrator.main_app.TicketBotOrchestrator.process_chat_message")
    def test_metrics_track_requests(
        self,
        mock_process: MagicMock,
        orchestrator_client: TestClient,
    ) -> None:
        """Test that metrics are collected for requests."""
        mock_process.return_value = {
            "success": True,
            "message": "Success",
            "data": None,
        }

        # Make a request
        orchestrator_client.post(
            "/process",
            json={
                "message": "Test command",
                "user_id": "test-user",
                "project_key": "TEST",
                "ai_provider": "claude",
            },
        )

        # Check metrics
        metrics_response = orchestrator_client.get("/metrics")
        metrics_text = metrics_response.text

        # Verify key metrics are present
        assert "orchestrator_requests_total" in metrics_text
        assert "orchestrator_request_duration_seconds" in metrics_text
        assert "orchestrator_requests_success_total" in metrics_text

    def test_health_check_integration(self, orchestrator_client: TestClient) -> None:
        """Test health check endpoint."""
        response = orchestrator_client.get("/health")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ticket-bot-orchestrator"

    def test_status_endpoint_shows_components(self, orchestrator_client: TestClient) -> None:
        """Test status endpoint shows available components."""
        response = orchestrator_client.get("/status")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "ai_provider_available" in data
        assert "ticket_service_available" in data
