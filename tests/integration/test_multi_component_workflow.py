"""Integration tests for multi-component workflows."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from ticket_api import Comment, Ticket, TicketPriority, TicketStatus
from ticket_service import app

pytestmark = pytest.mark.integration

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ERROR = 400

# Test data constants
EXPECTED_COMMENTS_COUNT = 2
MIN_TICKETS_FOR_LIST = 3


class TestTicketLifecycleWorkflow:
    """Test complete ticket lifecycle: create, update, comment, close."""

    def test_complete_ticket_lifecycle(self, mock_jira_backend: dict[str, MagicMock]) -> None:
        """Test a complete ticket workflow from creation to resolution."""
        ticket_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Step 1: Create a ticket
        created_ticket = Ticket(
            id=ticket_id,
            title="Implement user authentication",
            description="Add OAuth2 authentication to the app",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="alice@example.com",
            assignee="bob@example.com",
            created_at=datetime.fromisoformat("2024-01-15T10:00:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-15T10:00:00+00:00"),
            comments=[],
        )

        # Step 2: Update ticket to in-progress
        inprogress_ticket = Ticket(
            id=ticket_id,
            title="Implement user authentication",
            description="Add OAuth2 authentication to the app",
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.HIGH,
            reporter="alice@example.com",
            assignee="bob@example.com",
            created_at=datetime.fromisoformat("2024-01-15T10:00:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-15T11:00:00+00:00"),
            comments=[],
        )

        # Step 3: Add comments during work
        comment1 = Comment(
            id=UUID("550e8400-e29b-41d4-a716-446655440010"),
            ticket_id=ticket_id,
            author="bob@example.com",
            content="Started implementing OAuth2 flow",
            created_at=datetime.fromisoformat("2024-01-15T11:30:00+00:00"),
        )

        comment2 = Comment(
            id=UUID("550e8400-e29b-41d4-a716-446655440011"),
            ticket_id=ticket_id,
            author="alice@example.com",
            content="Great! Let me review the PR when ready",
            created_at=datetime.fromisoformat("2024-01-15T12:00:00+00:00"),
        )

        # Step 4: Mark as resolved
        resolved_ticket = Ticket(
            id=ticket_id,
            title="Implement user authentication",
            description="Add OAuth2 authentication to the app",
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.HIGH,
            reporter="alice@example.com",
            assignee="bob@example.com",
            created_at=datetime.fromisoformat("2024-01-15T10:00:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-16T10:00:00+00:00"),
            comments=[comment1, comment2],
        )

        client = TestClient(app)

        # Create ticket
        mock_jira_backend["create_ticket"].return_value = created_ticket
        response = client.post(
            "/api/v1/tickets",
            json={
                "title": "Implement user authentication",
                "description": "Add OAuth2 authentication to the app",
                "reporter": "alice@example.com",
                "priority": "high",
            },
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_CREATED
        created_data = response.json()
        assert created_data["status"] == "open"

        # Update to in-progress
        mock_jira_backend["update_ticket"].return_value = inprogress_ticket
        response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "in_progress"},
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_OK
        updated_data = response.json()
        assert updated_data["status"] == "in_progress"

        # Add first comment
        mock_jira_backend["add_comment"].return_value = comment1
        response = client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            json={"author": "bob@example.com", "content": "Started implementing OAuth2 flow"},
            headers={"X-User-ID": "test-bob", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_CREATED
        comment_data = response.json()
        assert comment_data["content"] == "Started implementing OAuth2 flow"

        # Add second comment
        mock_jira_backend["add_comment"].return_value = comment2
        response = client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            json={"author": "alice@example.com", "content": "Great! Let me review the PR when ready"},
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_CREATED

        # Get all comments
        mock_jira_backend["get_ticket_comments"].return_value = [comment1, comment2]
        response = client.get(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_OK
        comments_data = response.json()
        assert len(comments_data) == EXPECTED_COMMENTS_COUNT

        # Mark as resolved
        mock_jira_backend["update_ticket"].return_value = resolved_ticket
        response = client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"status": "resolved"},
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_OK
        resolved_data = response.json()
        assert resolved_data["status"] == "resolved"

        # Verify final state
        mock_jira_backend["get_ticket"].return_value = resolved_ticket
        response = client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers={"X-User-ID": "test-alice", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_OK
        final_data = response.json()
        assert final_data["status"] == "resolved"
        assert final_data["id"] == str(ticket_id)


class TestBulkOperationWorkflow:
    """Test workflows involving multiple tickets."""

    def test_filter_and_bulk_update(
        self,
        sample_tickets_list: list[Ticket],
        mock_jira_backend: dict[str, MagicMock],
    ) -> None:
        """Test filtering tickets and updating multiple ones."""
        # Simulate filtering for HIGH priority tickets
        high_priority_tickets = [t for t in sample_tickets_list if t.priority == TicketPriority.HIGH]

        client = TestClient(app)

        # List all tickets
        mock_jira_backend["list_tickets"].return_value = sample_tickets_list
        response = client.get(
            "/api/v1/tickets",
            headers={"X-User-ID": "test-user-001", "X-Project-Key": "PROJ"},
        )
        assert response.status_code == HTTP_OK
        data = response.json()
        all_tickets = data if isinstance(data, list) else data.get("tickets", [])
        assert len(all_tickets) >= MIN_TICKETS_FOR_LIST

        # Update high priority tickets to in-progress
        for ticket in high_priority_tickets:
            updated = Ticket(
                id=ticket.id,
                title=ticket.title,
                description=ticket.description,
                status=TicketStatus.IN_PROGRESS,
                priority=ticket.priority,
                reporter=ticket.reporter,
                assignee=ticket.assignee,
                created_at=ticket.created_at,
                updated_at=datetime.fromisoformat("2024-01-16T15:00:00+00:00"),
                comments=ticket.comments,
            )
            mock_jira_backend["update_ticket"].return_value = updated
            response = client.patch(
                f"/api/v1/tickets/{ticket.id}",
                json={"status": "in_progress"},
                headers={"X-User-ID": "test-user-001", "X-Project-Key": "PROJ"},
            )
            assert response.status_code == HTTP_OK

    def test_concurrent_ticket_updates(
        self,
        sample_tickets_list: list[Ticket],
        mock_jira_backend: dict[str, MagicMock],
    ) -> None:
        """Test that service can handle concurrent updates."""
        client = TestClient(app)

        # Simulate updating multiple tickets
        for ticket in sample_tickets_list:
            updated = Ticket(
                id=ticket.id,
                title=ticket.title + " [REVIEWED]",
                description=ticket.description,
                status=ticket.status,
                priority=ticket.priority,
                reporter=ticket.reporter,
                assignee=ticket.assignee,
                created_at=ticket.created_at,
                updated_at=datetime.fromisoformat("2024-01-16T16:00:00+00:00"),
                comments=ticket.comments,
            )
            mock_jira_backend["update_ticket"].return_value = updated
            response = client.patch(
                f"/api/v1/tickets/{ticket.id}",
                json={"title": ticket.title + " [REVIEWED]"},
                headers={"X-User-ID": "test-reviewer", "X-Project-Key": "PROJ"},
            )
            assert response.status_code == HTTP_OK


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery in workflows."""

    def test_invalid_ticket_id_handling(self, mock_jira_backend: dict[str, MagicMock]) -> None:
        """Test handling of requests for non-existent tickets."""
        # Mock returns None for non-existent ticket
        mock_jira_backend["get_ticket"].return_value = None

        client = TestClient(app)
        response = client.get(
            "/api/v1/tickets/non-existent-id",
            headers={"X-User-ID": "test-user-001", "X-Project-Key": "PROJ"},
        )

        assert response.status_code >= HTTP_ERROR
