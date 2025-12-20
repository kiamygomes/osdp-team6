"""Tests for additional RemoteTicketService methods."""

from uuid import uuid4

import httpx
import pytest
import respx
from ticket_api import TicketPriority, TicketStatus

from ticket_client_adapter import RemoteTicketService

BASE_URL = "http://test-server:8000"
TEST_USER = "test-user"
TEST_PROJECT = "TEST"


@pytest.mark.asyncio
@respx.mock
async def test_transition_status() -> None:
    """Test transitioning ticket status."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(ticket_id),
                "title": "Test",
                "description": "Test",
                "status": "in_progress",
                "priority": "medium",
                "reporter": "test@example.com",
                "assignee": None,
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.transition_status(ticket_id, TicketStatus.IN_PROGRESS)
        assert ticket is not None
        assert ticket.status == TicketStatus.IN_PROGRESS


@pytest.mark.asyncio
@respx.mock
async def test_transition_status_not_found() -> None:
    """Test transitioning status for non-existent ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.transition_status(ticket_id, TicketStatus.IN_PROGRESS)
        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_reassign_ticket() -> None:
    """Test reassigning a ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(ticket_id),
                "title": "Test",
                "description": "Test",
                "status": "open",
                "priority": "medium",
                "reporter": "test@example.com",
                "assignee": "new@example.com",
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.reassign_ticket(ticket_id, "new@example.com")
        assert ticket is not None
        assert ticket.assignee == "new@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_reassign_ticket_not_found() -> None:
    """Test reassigning non-existent ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.reassign_ticket(ticket_id, "new@example.com")
        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_update_priority() -> None:
    """Test updating ticket priority."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(ticket_id),
                "title": "Test",
                "description": "Test",
                "status": "open",
                "priority": "high",
                "reporter": "test@example.com",
                "assignee": None,
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.update_priority(ticket_id, TicketPriority.HIGH)
        assert ticket is not None
        assert ticket.priority == TicketPriority.HIGH


@pytest.mark.asyncio
@respx.mock
async def test_update_priority_not_found() -> None:
    """Test updating priority for non-existent ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.update_priority(ticket_id, TicketPriority.HIGH)
        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_update_description() -> None:
    """Test updating ticket description."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(ticket_id),
                "title": "Test",
                "description": "Updated description",
                "status": "open",
                "priority": "medium",
                "reporter": "test@example.com",
                "assignee": None,
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.update_description(ticket_id, "Updated description")
        assert ticket is not None
        assert ticket.description == "Updated description"


@pytest.mark.asyncio
@respx.mock
async def test_update_description_not_found() -> None:
    """Test updating description for non-existent ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.update_description(ticket_id, "Updated description")
        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_retry_with_backoff_calculation() -> None:
    """Test that retry backoff is calculated correctly."""
    call_count = 0
    max_failures = 2
    expected_total_calls = 3

    def response_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count <= max_failures:
            return httpx.Response(503, json={"detail": "Service unavailable"})
        return httpx.Response(
            201,
            json={
                "id": str(uuid4()),
                "title": "Test",
                "description": "Test",
                "status": "open",
                "priority": "medium",
                "reporter": "test@example.com",
                "assignee": None,
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        )

    respx.post(f"{BASE_URL}/api/v1/tickets").mock(side_effect=response_handler)

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
        max_retries=3,
        initial_backoff_seconds=0.01,  # Fast for testing
    ) as service:
        ticket = await service.create_ticket(
            title="Test",
            description="Test",
            reporter="test@example.com",
        )
        assert ticket.title == "Test"
        assert call_count == expected_total_calls  # Initial + 2 retries


@pytest.mark.asyncio
@respx.mock
async def test_delete_ticket_success() -> None:
    """Test successful ticket deletion."""
    ticket_id = uuid4()
    respx.delete(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(204),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.delete_ticket(ticket_id)
        assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_delete_ticket_not_found() -> None:
    """Test deleting non-existent ticket."""
    ticket_id = uuid4()
    respx.delete(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.delete_ticket(ticket_id)
        assert result is False


@pytest.mark.asyncio
@respx.mock
async def test_add_comment_success() -> None:
    """Test adding a comment to a ticket."""
    ticket_id = uuid4()
    comment_id = uuid4()
    respx.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": str(comment_id),
                "ticket_id": str(ticket_id),
                "author": "test@example.com",
                "content": "Test comment",
                "created_at": "2025-10-29T00:00:00Z",
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        comment = await service.add_comment(
            ticket_id=ticket_id,
            author="test@example.com",
            content="Test comment",
        )
        assert comment is not None
        assert comment.content == "Test comment"
        assert comment.author == "test@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_comments() -> None:
    """Test retrieving comments for a ticket."""
    ticket_id = uuid4()
    comment_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": str(comment_id),
                    "ticket_id": str(ticket_id),
                    "author": "test@example.com",
                    "content": "Test comment",
                    "created_at": "2025-10-29T00:00:00Z",
                },
            ],
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        comments = await service.get_ticket_comments(ticket_id)
        assert len(comments) == 1
        assert comments[0].content == "Test comment"


@pytest.mark.asyncio
@respx.mock
async def test_add_comment_not_found() -> None:
    """Test adding comment to non-existent ticket."""
    ticket_id = uuid4()
    respx.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(404, json={"detail": "Not found"}),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        result = await service.add_comment(
            ticket_id=ticket_id,
            author="test@example.com",
            content="Test comment",
        )
        assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_comments_empty() -> None:
    """Test retrieving comments for ticket with no comments."""
    ticket_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(200, json=[]),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        comments = await service.get_ticket_comments(ticket_id)
        assert len(comments) == 0


@pytest.mark.asyncio
@respx.mock
async def test_list_tickets_empty() -> None:
    """Test listing tickets when none exist."""
    respx.get(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(
            200,
            json={
                "tickets": [],
                "total": 0,
                "limit": 100,
                "offset": 0,
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        tickets = await service.list_tickets()
        assert len(tickets) == 0


@pytest.mark.asyncio
@respx.mock
async def test_update_ticket_partial() -> None:
    """Test updating only some fields of a ticket."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(ticket_id),
                "title": "Updated Title",
                "description": "Original description",
                "status": "open",
                "priority": "medium",
                "reporter": "test@example.com",
                "assignee": None,
                "created_at": "2025-10-29T00:00:00Z",
                "updated_at": "2025-10-29T00:00:00Z",
                "comments": [],
            },
        ),
    )

    async with RemoteTicketService(
        base_url=BASE_URL,
        user_id=TEST_USER,
        project_key=TEST_PROJECT,
    ) as service:
        ticket = await service.update_ticket(
            ticket_id=ticket_id,
            title="Updated Title",
        )
        assert ticket is not None
        assert ticket.title == "Updated Title"
