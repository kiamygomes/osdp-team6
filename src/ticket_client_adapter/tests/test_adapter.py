"""Tests for RemoteTicketService adapter using respx to mock HTTP calls."""

from uuid import UUID, uuid4

import httpx
import pytest
import respx

from ticket_api import TicketPriority, TicketStatus
from ticket_client_adapter import RemoteTicketService

BASE_URL = "http://test-server:8000"
TEST_USER = "test-user"
TEST_PROJECT = "TEST"
EXPECTED_COMMENT_COUNT = 2


@pytest.fixture
def mock_ticket_id() -> UUID:
    """Fixture providing a test ticket UUID."""
    return uuid4()


@pytest.fixture
def mock_ticket_data(mock_ticket_id: UUID) -> dict[str, object]:
    """Fixture providing mock ticket response data."""
    return {
        "id": str(mock_ticket_id),
        "title": "Test Ticket",
        "description": "Test description",
        "status": "open",
        "priority": "medium",
        "reporter": "reporter@example.com",
        "assignee": None,
        "created_at": "2025-10-29T00:00:00Z",
        "updated_at": "2025-10-29T00:00:00Z",
        "comments": [],
    }


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_create_ticket(mock_ticket_data: dict[str, object]) -> None:
    """Test creating a ticket via the adapter."""
    # Mock the HTTP POST request
    route = respx.post(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(201, json=mock_ticket_data),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.create_ticket(
            title="Test Ticket",
            description="Test description",
            reporter="reporter@example.com",
            priority=TicketPriority.MEDIUM,
        )

        assert ticket.title == "Test Ticket"
        assert ticket.description == "Test description"
        assert ticket.priority == TicketPriority.MEDIUM
        assert ticket.status == TicketStatus.OPEN

        # Verify the request was made with correct headers
        assert route.called
        request = route.calls.last.request
        assert request.headers["X-User-ID"] == TEST_USER
        assert request.headers["X-Project-Key"] == TEST_PROJECT


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_get_ticket(mock_ticket_id: UUID, mock_ticket_data: dict[str, object]) -> None:
    """Test retrieving a ticket by ID."""
    respx.get(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}").mock(
        return_value=httpx.Response(200, json=mock_ticket_data),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.get_ticket(mock_ticket_id)

        assert ticket is not None
        assert ticket.id == mock_ticket_id
        assert ticket.title == "Test Ticket"


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_get_ticket_not_found(mock_ticket_id: UUID) -> None:
    """Test retrieving a non-existent ticket returns None."""
    respx.get(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.get_ticket(mock_ticket_id)

        assert ticket is None


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_list_tickets(mock_ticket_data: dict[str, object]) -> None:
    """Test listing tickets with filters."""
    list_response = {
        "tickets": [mock_ticket_data],
        "total": 1,
        "limit": 100,
        "offset": 0,
    }

    respx.get(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(200, json=list_response),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        tickets = await service.list_tickets(
            status=TicketStatus.OPEN,
            limit=10,
        )

        assert len(tickets) == 1
        assert tickets[0].title == "Test Ticket"


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_update_ticket(mock_ticket_id: UUID, mock_ticket_data: dict[str, object]) -> None:
    """Test updating a ticket."""
    updated_data = {**mock_ticket_data, "title": "Updated Title", "status": "in_progress"}

    respx.patch(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}").mock(
        return_value=httpx.Response(200, json=updated_data),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.update_ticket(
            ticket_id=mock_ticket_id,
            title="Updated Title",
            status=TicketStatus.IN_PROGRESS,
        )

        assert ticket is not None
        assert ticket.title == "Updated Title"
        assert ticket.status == TicketStatus.IN_PROGRESS


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_delete_ticket(mock_ticket_id: UUID) -> None:
    """Test deleting a ticket."""
    respx.delete(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}").mock(
        return_value=httpx.Response(204),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        success = await service.delete_ticket(mock_ticket_id)

        assert success is True


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_delete_ticket_not_found(mock_ticket_id: UUID) -> None:
    """Test deleting a non-existent ticket returns False."""
    respx.delete(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}").mock(
        return_value=httpx.Response(404),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        success = await service.delete_ticket(mock_ticket_id)

        assert success is False


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_add_comment(mock_ticket_id: UUID) -> None:
    """Test adding a comment to a ticket."""
    comment_data = {
        "id": str(uuid4()),
        "ticket_id": str(mock_ticket_id),
        "author": "dev@example.com",
        "content": "This is a comment",
        "created_at": "2025-10-29T00:00:00Z",
    }

    respx.post(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}/comments").mock(
        return_value=httpx.Response(201, json=comment_data),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        comment = await service.add_comment(
            ticket_id=mock_ticket_id,
            author="dev@example.com",
            content="This is a comment",
        )

        assert comment is not None
        assert comment.author == "dev@example.com"
        assert comment.content == "This is a comment"


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_get_ticket_comments(mock_ticket_id: UUID) -> None:
    """Test retrieving all comments for a ticket."""
    comments_data = [
        {
            "id": str(uuid4()),
            "ticket_id": str(mock_ticket_id),
            "author": "user1@example.com",
            "content": "First comment",
            "created_at": "2025-10-29T00:00:00Z",
        },
        {
            "id": str(uuid4()),
            "ticket_id": str(mock_ticket_id),
            "author": "user2@example.com",
            "content": "Second comment",
            "created_at": "2025-10-29T00:01:00Z",
        },
    ]

    respx.get(f"{BASE_URL}/api/v1/tickets/{mock_ticket_id}/comments").mock(
        return_value=httpx.Response(200, json=comments_data),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        comments = await service.get_ticket_comments(mock_ticket_id)

        assert len(comments) == EXPECTED_COMMENT_COUNT
        assert comments[0].author == "user1@example.com"
        assert comments[1].author == "user2@example.com"


@pytest.mark.asyncio
async def test_context_manager() -> None:
    """Test that adapter properly handles async context manager."""
    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        assert service is not None
        assert isinstance(service, RemoteTicketService)
