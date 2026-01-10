"""Test error handling in RemoteTicketService adapter."""

from http import HTTPStatus
from uuid import uuid4

import httpx
import pytest
import respx

from ticket_client_adapter import RemoteTicketService

BASE_URL = "http://test-server:8000"
TEST_USER = "test-user"
TEST_PROJECT = "TEST"


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_http_error() -> None:
    """Test creating a ticket with HTTP error response."""
    respx.post(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to create ticket"):
            await service.create_ticket(
                title="Test",
                description="Test",
                reporter="test@example.com",
            )


@pytest.mark.asyncio
@respx.mock
async def test_get_ticket_http_error() -> None:
    """Test getting a ticket with HTTP error response."""
    ticket_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to get ticket"):
            await service.get_ticket(ticket_id)


@pytest.mark.asyncio
@respx.mock
async def test_list_tickets_http_error() -> None:
    """Test listing tickets with HTTP error response."""
    respx.get(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to list tickets"):
            await service.list_tickets()


@pytest.mark.asyncio
@respx.mock
async def test_update_ticket_http_error() -> None:
    """Test updating a ticket with HTTP error response."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to update ticket"):
            await service.update_ticket(ticket_id, title="New Title")


@pytest.mark.asyncio
@respx.mock
async def test_delete_ticket_http_error() -> None:
    """Test deleting a ticket with HTTP error response."""
    ticket_id = uuid4()
    respx.delete(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to delete ticket"):
            await service.delete_ticket(ticket_id)


@pytest.mark.asyncio
@respx.mock
async def test_add_comment_http_error() -> None:
    """Test adding a comment with HTTP error response."""
    ticket_id = uuid4()
    respx.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to add comment"):
            await service.add_comment(ticket_id, "author@example.com", "Comment")


@pytest.mark.asyncio
@respx.mock
async def test_get_comments_http_error() -> None:
    """Test getting comments with HTTP error response."""
    ticket_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(500, json={"detail": "Internal server error"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError, match="Failed to get comments"):
            await service.get_ticket_comments(ticket_id)


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_bad_request() -> None:
    """Test creating a ticket with 400 Bad Request."""
    respx.post(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(400, json={"detail": "Invalid data"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError):
            await service.create_ticket(
                title="Test",
                description="Test",
                reporter="test@example.com",
            )


@pytest.mark.asyncio
@respx.mock
async def test_update_ticket_bad_request() -> None:
    """Test updating a ticket with 400 Bad Request."""
    ticket_id = uuid4()
    respx.patch(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(400, json={"detail": "Invalid data"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError):
            await service.update_ticket(ticket_id, title="New Title")


@pytest.mark.asyncio
@respx.mock
async def test_delete_ticket_forbidden() -> None:
    """Test deleting a ticket with 403 Forbidden."""
    ticket_id = uuid4()
    respx.delete(f"{BASE_URL}/api/v1/tickets/{ticket_id}").mock(
        return_value=httpx.Response(403, json={"detail": "Forbidden"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError):
            await service.delete_ticket(ticket_id)


@pytest.mark.asyncio
@respx.mock
async def test_add_comment_bad_request() -> None:
    """Test adding a comment with 400 Bad Request."""
    ticket_id = uuid4()
    respx.post(f"{BASE_URL}/api/v1/tickets/{ticket_id}/comments").mock(
        return_value=httpx.Response(400, json={"detail": "Invalid comment"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT) as service:
        with pytest.raises(httpx.HTTPStatusError):
            await service.add_comment(ticket_id, "author@example.com", "Comment")


@pytest.mark.asyncio
async def test_create_ticket_wrong_response_type() -> None:
    """Test create_ticket when response.parsed is not TicketResponse."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)

    # Mock the generated client to return wrong type
    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.CREATED
    mock_response.parsed = {"wrong": "type"}  # Not a TicketResponse instance

    with respx.mock:
        # Replace the function with a mock that returns our bad response
        import ticket_service_client.api.tickets.create_ticket_api_v1_tickets_post as create_module

        original_func = create_module.asyncio_detailed
        create_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.create_ticket("Test", "Desc", "reporter@example.com")
        finally:
            create_module.asyncio_detailed = original_func


@pytest.mark.asyncio
async def test_get_ticket_wrong_response_type() -> None:
    """Test get_ticket when response.parsed is not TicketResponse."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)
    ticket_id = uuid4()

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.parsed = {"wrong": "type"}

    with respx.mock:
        import ticket_service_client.api.tickets.get_ticket_api_v1_tickets_ticket_id_get as get_module

        original_func = get_module.asyncio_detailed
        get_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.get_ticket(ticket_id)
        finally:
            get_module.asyncio_detailed = original_func


@pytest.mark.asyncio
async def test_list_tickets_wrong_response_type() -> None:
    """Test list_tickets when response.parsed is not TicketListResponse."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.parsed = {"wrong": "type"}

    with respx.mock:
        import ticket_service_client.api.tickets.list_tickets_api_v1_tickets_get as list_module

        original_func = list_module.asyncio_detailed
        list_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.list_tickets()
        finally:
            list_module.asyncio_detailed = original_func


@pytest.mark.asyncio
async def test_update_ticket_wrong_response_type() -> None:
    """Test update_ticket when response.parsed is not TicketResponse."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)
    ticket_id = uuid4()

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.parsed = {"wrong": "type"}

    with respx.mock:
        import ticket_service_client.api.tickets.update_ticket_api_v1_tickets_ticket_id_patch as update_module

        original_func = update_module.asyncio_detailed
        update_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.update_ticket(ticket_id, title="New")
        finally:
            update_module.asyncio_detailed = original_func


@pytest.mark.asyncio
async def test_add_comment_wrong_response_type() -> None:
    """Test add_comment when response.parsed is not CommentResponse."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)
    ticket_id = uuid4()

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.CREATED
    mock_response.parsed = {"wrong": "type"}

    with respx.mock:
        import ticket_service_client.api.comments.add_comment_api_v1_tickets_ticket_id_comments_post as add_module

        original_func = add_module.asyncio_detailed
        add_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.add_comment(ticket_id, "author", "content")
        finally:
            add_module.asyncio_detailed = original_func


@pytest.mark.asyncio
async def test_get_comments_wrong_response_type() -> None:
    """Test get_ticket_comments when response.parsed is not a list."""
    from unittest.mock import AsyncMock, MagicMock

    service = RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT)
    ticket_id = uuid4()

    mock_response = MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.parsed = {"wrong": "type"}  # Not a list

    with respx.mock:
        import ticket_service_client.api.comments.get_ticket_comments_api_v1_tickets_ticket_id_comments_get as get_comments_module

        original_func = get_comments_module.asyncio_detailed
        get_comments_module.asyncio_detailed = AsyncMock(return_value=mock_response)

        try:
            with pytest.raises(TypeError, match="Unexpected response type"):
                await service.get_ticket_comments(ticket_id)
        finally:
            get_comments_module.asyncio_detailed = original_func


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_with_retry_on_server_error() -> None:
    """Test that create_ticket retries on 5xx errors."""
    from uuid import uuid4

    ticket_id = uuid4()
    route = respx.post(f"{BASE_URL}/api/v1/tickets")
    # First attempt returns 503, second succeeds
    route.side_effect = [
        httpx.Response(503, json={"detail": "Service unavailable"}),
        httpx.Response(
            201,
            json={
                "id": str(ticket_id),
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
        ),
    ]

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT, max_retries=3, initial_backoff_seconds=0.01) as service:
        # This should retry and succeed
        ticket = await service.create_ticket(
            title="Test",
            description="Test",
            reporter="test@example.com",
        )
        assert ticket.title == "Test"


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_with_429_retry() -> None:
    """Test that create_ticket retries on 429 (Too Many Requests)."""
    from uuid import uuid4

    ticket_id = uuid4()
    route = respx.post(f"{BASE_URL}/api/v1/tickets")
    # First attempt returns 429, second succeeds
    route.side_effect = [
        httpx.Response(429, json={"detail": "Too many requests"}),
        httpx.Response(
            201,
            json={
                "id": str(ticket_id),
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
        ),
    ]

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT, max_retries=3, initial_backoff_seconds=0.01) as service:
        # This should retry and succeed
        ticket = await service.create_ticket(
            title="Test",
            description="Test",
            reporter="test@example.com",
        )
        assert ticket.title == "Test"


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_retries_exhausted() -> None:
    """Test that create_ticket raises after retries exhausted."""
    respx.post(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(503, json={"detail": "Service unavailable"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT, max_retries=2, initial_backoff_seconds=0.01) as service:
        # Should raise after 2 retries (all attempts fail)
        with pytest.raises(httpx.HTTPStatusError):
            await service.create_ticket(
                title="Test",
                description="Test",
                reporter="test@example.com",
            )


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_client_error_no_retry() -> None:
    """Test that create_ticket doesn't retry on 4xx client errors."""
    respx.post(f"{BASE_URL}/api/v1/tickets").mock(
        return_value=httpx.Response(400, json={"detail": "Bad request"}),
    )

    async with RemoteTicketService(BASE_URL, TEST_USER, TEST_PROJECT, max_retries=3, initial_backoff_seconds=0.01) as service:
        # Should immediately raise without retrying on 4xx errors
        with pytest.raises(httpx.HTTPStatusError, match="Failed to create ticket"):
            await service.create_ticket(
                title="Test",
                description="Test",
                reporter="test@example.com",
            )
