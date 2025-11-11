"""Tests for RemoteTicketService adapter using respx to mock HTTP calls."""

from typing import Any
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
def mock_ticket_data(mock_ticket_id: UUID) -> dict[str, Any]:
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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
@respx.mock
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


@pytest.mark.asyncio
@respx.mock
async def test_transition_status(mock_ticket_data: dict[str, Any]) -> None:
    """Test transitioning a ticket status."""
    ticket_id = UUID(str(mock_ticket_data["id"]))
    updated_data = dict(mock_ticket_data)
    updated_data["status"] = "in_progress"

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(200, json=updated_data),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.transition_status(ticket_id, TicketStatus.IN_PROGRESS)

        assert result is not None
        assert result.status == TicketStatus.IN_PROGRESS


@pytest.mark.asyncio
@respx.mock
async def test_reassign_ticket(mock_ticket_data: dict[str, Any]) -> None:
    """Test reassigning a ticket."""
    ticket_id = UUID(str(mock_ticket_data["id"]))
    updated_data = dict(mock_ticket_data)
    updated_data["assignee"] = "newassignee@example.com"

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(200, json=updated_data),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.reassign_ticket(ticket_id, "newassignee@example.com")

        assert result is not None
        assert result.assignee == "newassignee@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_update_priority(mock_ticket_data: dict[str, Any]) -> None:
    """Test updating a ticket priority."""
    ticket_id = UUID(str(mock_ticket_data["id"]))
    updated_data = dict(mock_ticket_data)
    updated_data["priority"] = "high"

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(200, json=updated_data),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.update_priority(ticket_id, TicketPriority.HIGH)

        assert result is not None
        assert result.priority == TicketPriority.HIGH


@pytest.mark.asyncio
@respx.mock
async def test_update_description(mock_ticket_data: dict[str, Any]) -> None:
    """Test updating a ticket description."""
    ticket_id = UUID(str(mock_ticket_data["id"]))
    new_description = "Updated description"
    updated_data = dict(mock_ticket_data)
    updated_data["description"] = new_description

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(200, json=updated_data),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.update_description(ticket_id, new_description)

        assert result is not None
        assert result.description == new_description


@pytest.mark.asyncio
async def test_idempotent_client_set_idempotency_key() -> None:
    """Test setting idempotency key on IdempotentClient."""
    from ticket_client_adapter.client import IdempotentClient

    client = IdempotentClient(base_url=BASE_URL)
    test_key = "test-idempotency-key-123"

    client.set_idempotency_key(test_key)
    assert client._idempotency_key == test_key


@pytest.mark.asyncio
async def test_idempotent_client_clear_idempotency_key() -> None:
    """Test clearing idempotency key on IdempotentClient."""
    from ticket_client_adapter.client import IdempotentClient

    client = IdempotentClient(base_url=BASE_URL)
    test_key = "test-idempotency-key-456"

    client.set_idempotency_key(test_key)
    assert client._idempotency_key == test_key

    client.clear_idempotency_key()
    assert client._idempotency_key is None


@pytest.mark.asyncio
async def test_idempotent_client_get_async_httpx_client() -> None:
    """Test getting async httpx client from IdempotentClient."""
    from ticket_client_adapter.client import IdempotentClient

    client = IdempotentClient(base_url=BASE_URL)
    http_client = client.get_async_httpx_client()

    assert isinstance(http_client, httpx.AsyncClient)
    await http_client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_update_ticket_not_found() -> None:
    """Test updating a non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.update_ticket(ticket_id, title="New Title")

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_transition_status_not_found() -> None:
    """Test transitioning status of non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.transition_status(ticket_id, TicketStatus.CLOSED)

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_reassign_ticket_not_found() -> None:
    """Test reassigning non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.reassign_ticket(ticket_id, "new@example.com")

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_update_priority_not_found() -> None:
    """Test updating priority of non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.update_priority(ticket_id, TicketPriority.HIGH)

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_update_description_not_found() -> None:
    """Test updating description of non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.update_description(ticket_id, "New description")

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_add_comment_not_found() -> None:
    """Test adding comment to non-existent ticket returns None."""
    ticket_id = uuid4()

    respx.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(404, json={"detail": "Ticket not found"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        result = await service.add_comment(ticket_id, "author@example.com", "Comment content")

        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_list_tickets_error() -> None:
    """Test listing tickets with error response."""
    respx.get(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to list tickets"):
            await service.list_tickets()
