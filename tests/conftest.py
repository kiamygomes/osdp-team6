"""Shared fixtures for integration and e2e tests."""

import asyncio
from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from ticket_impl.config import settings

from ticket_api import Comment, Ticket, TicketPriority, TicketServiceAPI, TicketStatus

# Verify settings are loaded (ensures .env is processed)
assert settings.db_url is not None


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_token_storage(request: pytest.FixtureRequest) -> Generator[MagicMock | None, None, None]:
    """Auto-patch token storage to allow test users.

    Note: This fixture is skipped for e2e tests which use real OAuth tokens.
    """
    # Skip mocking for e2e tests
    if "e2e" in request.keywords:
        yield None
        return

    with patch("ticket_service.main.get_user_tokens") as mock_get_tokens:
        # Allow test- prefixed users to pass token verification
        mock_get_tokens.return_value = {"access_token": "test-token"}
        yield mock_get_tokens


@pytest.fixture(autouse=True)
def mock_jira_backend(request: pytest.FixtureRequest) -> Generator[dict[str, MagicMock | None], None, None]:
    """Auto-patch Jira backend to prevent actual API calls.

    Note: This fixture is skipped for e2e tests which need real API calls.
    """
    # Skip mocking for e2e tests
    if "e2e" in request.keywords:
        yield {
            "create_ticket": None,
            "get_ticket": None,
            "list_tickets": None,
            "update_ticket": None,
            "delete_ticket": None,
            "add_comment": None,
            "get_ticket_comments": None,
        }
        return

    with (
        patch("ticket_impl.impl.TicketImpl.create_ticket") as mock_create,
        patch("ticket_impl.impl.TicketImpl.get_ticket") as mock_get,
        patch("ticket_impl.impl.TicketImpl.list_tickets") as mock_list,
        patch("ticket_impl.impl.TicketImpl.update_ticket") as mock_update,
        patch("ticket_impl.impl.TicketImpl.delete_ticket") as mock_delete,
        patch("ticket_impl.impl.TicketImpl.add_comment") as mock_add_comment,
        patch("ticket_impl.impl.TicketImpl.get_ticket_comments") as mock_get_comments,
    ):
        # Set default return values - will be overridden in individual tests
        mock_create.return_value = None
        mock_get.return_value = None
        mock_list.return_value = []
        mock_update.return_value = None
        mock_delete.return_value = None
        mock_add_comment.return_value = None
        mock_get_comments.return_value = []

        yield {
            "create_ticket": mock_create,
            "get_ticket": mock_get,
            "list_tickets": mock_list,
            "update_ticket": mock_update,
            "delete_ticket": mock_delete,
            "add_comment": mock_add_comment,
            "get_ticket_comments": mock_get_comments,
        }


@pytest.fixture
def mock_ticket_service() -> MagicMock:
    """Create a mock TicketServiceAPI implementation."""
    return AsyncMock(spec=TicketServiceAPI)


@pytest.fixture
def sample_ticket() -> Ticket:
    """Create a sample ticket for testing."""
    return Ticket(
        id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        title="Fix login bug",
        description="Users cannot login on mobile",
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        reporter="john@example.com",
        assignee="jane@example.com",
        created_at=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
        updated_at=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
        comments=[],
    )


@pytest.fixture
def sample_ticket_with_comments() -> Ticket:
    """Create a sample ticket with comments for testing."""
    ticket_id = UUID("550e8400-e29b-41d4-a716-446655440001")
    return Ticket(
        id=ticket_id,
        title="Database optimization",
        description="Queries are too slow",
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.MEDIUM,
        reporter="bob@example.com",
        assignee="alice@example.com",
        created_at=datetime.fromisoformat("2024-01-10T14:20:00+00:00"),
        updated_at=datetime.fromisoformat("2024-01-16T09:15:00+00:00"),
        comments=[
            Comment(
                id=UUID("550e8400-e29b-41d4-a716-446655440010"),
                ticket_id=ticket_id,
                author="bob@example.com",
                content="Started investigating the slow queries",
                created_at=datetime.fromisoformat("2024-01-11T10:00:00+00:00"),
            ),
            Comment(
                id=UUID("550e8400-e29b-41d4-a716-446655440011"),
                ticket_id=ticket_id,
                author="alice@example.com",
                content="I've added indexes to the problematic tables",
                created_at=datetime.fromisoformat("2024-01-16T09:15:00+00:00"),
            ),
        ],
    )


@pytest.fixture
def sample_tickets_list() -> list[Ticket]:
    """Create a list of sample tickets for testing."""
    return [
        Ticket(
            id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="Fix login bug",
            description="Users cannot login on mobile",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="john@example.com",
            assignee="jane@example.com",
            created_at=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-15T10:30:00+00:00"),
            comments=[],
        ),
        Ticket(
            id=UUID("550e8400-e29b-41d4-a716-446655440001"),
            title="Database optimization",
            description="Queries are too slow",
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.MEDIUM,
            reporter="bob@example.com",
            assignee="alice@example.com",
            created_at=datetime.fromisoformat("2024-01-10T14:20:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-16T09:15:00+00:00"),
            comments=[],
        ),
        Ticket(
            id=UUID("550e8400-e29b-41d4-a716-446655440002"),
            title="Add user profile page",
            description="Users need a profile page",
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.MEDIUM,
            reporter="charlie@example.com",
            assignee="dave@example.com",
            created_at=datetime.fromisoformat("2024-01-05T08:00:00+00:00"),
            updated_at=datetime.fromisoformat("2024-01-14T16:45:00+00:00"),
            comments=[],
        ),
    ]
