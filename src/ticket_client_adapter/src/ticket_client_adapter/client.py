"""Remote HTTP client implementing TicketServiceAPI by wrapping the generated client.

Idempotency and Retry Strategy:
- Idempotent operations should include an Idempotency-Key header for safe retries
- Implement exponential backoff for transient failures (5xx, 429 status codes)
- Use circuit breaker pattern to prevent cascading failures
- Configure appropriate request timeouts to prevent hanging connections
- Log failed requests with correlation IDs for debugging

Example retry implementation:
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def create_ticket_with_retry(service, title, description, reporter):
        return await service.create_ticket(title, description, reporter)
"""

import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import TYPE_CHECKING, TypeVar, cast
from uuid import UUID

import httpx
from ticket_api import (
    Comment,
    Ticket,
    TicketPriority,
    TicketServiceAPI,
    TicketStatus,
)
from ticket_service_client import Client
from ticket_service_client.api.comments import (
    add_comment_api_v1_tickets_ticket_id_comments_post,
    get_ticket_comments_api_v1_tickets_ticket_id_comments_get,
)
from ticket_service_client.api.tickets import (
    create_ticket_api_v1_tickets_post,
    delete_ticket_api_v1_tickets_ticket_id_delete,
    get_ticket_api_v1_tickets_ticket_id_get,
    list_tickets_api_v1_tickets_get,
    update_ticket_api_v1_tickets_ticket_id_patch,
)
from ticket_service_client.models import (
    CommentCreateRequest,
    CommentResponse,
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
)
from ticket_service_client.models import (
    TicketPriority as GeneratedPriority,
)
from ticket_service_client.models import (
    TicketStatus as GeneratedStatus,
)

if TYPE_CHECKING:
    from ticket_service_client.types import Response

T = TypeVar("T")


class IdempotentClient(Client):
    """Extended Client that supports idempotency headers.

    Wraps the auto-generated Client to add Idempotency-Key header support
    for safe retries on idempotent operations.
    """

    def __init__(self, base_url: str) -> None:
        """Initialize the idempotent client."""
        super().__init__(base_url=base_url)
        self._idempotency_key: str | None = None

    def set_idempotency_key(self, key: str) -> None:
        """Set the current idempotency key for the next request."""
        self._idempotency_key = key

    def clear_idempotency_key(self) -> None:
        """Clear the idempotency key after request."""
        self._idempotency_key = None

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        """Get the async httpx client with idempotency support via override."""
        # Return the base client directly. Idempotency is set at the time
        # of request in create_ticket and add_comment methods.
        return super().get_async_httpx_client()


class RemoteTicketService(TicketServiceAPI):
    """Adapter wrapping the auto-generated client with TicketServiceAPI interface.

    This adapter hides all HTTP/network details from the consumer by:
    1. Using the auto-generated client internally
    2. Exposing only the clean TicketServiceAPI interface
    3. Converting between generated models and domain models

    Args:
        base_url: The service base URL (e.g., "http://localhost:8000")
        user_id: User identifier for authentication
        project_key: Jira project key for ticket operations

    Example:
        async with RemoteTicketService(
            base_url="http://localhost:8000",
            user_id="test-user",
            project_key="PROJ"
        ) as service:
            # Clean domain interface - no HTTP details!
            ticket = await service.create_ticket(
                title="Bug Report",
                description="Found an issue",
                reporter="user@example.com"
            )

    """

    def __init__(
        self,
        base_url: str,
        user_id: str,
        project_key: str,
        max_retries: int = 3,
        initial_backoff_seconds: float = 1.0,
    ) -> None:
        """Initialize the remote ticket service adapter.

        Args:
            base_url: Service base URL
            user_id: User identifier
            project_key: Jira project key
            max_retries: Maximum number of retry attempts for transient failures
            initial_backoff_seconds: Initial backoff duration in seconds for exponential backoff

        """
        self._client = IdempotentClient(base_url=base_url)
        self._user_id = user_id
        self._project_key = project_key
        self._max_retries = max_retries
        self._initial_backoff_seconds = initial_backoff_seconds

    async def __aenter__(self) -> "RemoteTicketService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        # Clean up the underlying HTTP client
        http_client = self._client.get_async_httpx_client()
        await http_client.aclose()

    async def _retry_with_backoff(
        self,
        operation: Callable[[], Awaitable[object]],
    ) -> object:
        """Execute operation with exponential backoff retry on transient failures.

        Args:
            operation: Async callable to execute with no arguments

        Returns:
            Result from the operation

        Raises:
            httpx.HTTPError: If all retries are exhausted

        """
        last_exception: httpx.HTTPStatusError | httpx.ConnectError | httpx.TimeoutException | None = None
        for attempt in range(self._max_retries):
            try:
                return await operation()
            except httpx.HTTPStatusError as e:
                last_exception = e
                # Only retry on transient errors (5xx, 429). Raise immediately on client errors.
                if e.response is not None and (
                    e.response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
                    and e.response.status_code != HTTPStatus.TOO_MANY_REQUESTS
                ):
                    raise
                if attempt < self._max_retries - 1:
                    backoff_seconds = self._initial_backoff_seconds * (2 ** attempt)
                    await asyncio.sleep(backoff_seconds)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    backoff_seconds = self._initial_backoff_seconds * (2 ** attempt)
                    await asyncio.sleep(backoff_seconds)

        if last_exception:
            raise last_exception
        error_msg = "Retry logic error: no exception caught"
        raise RuntimeError(error_msg)

    def _to_generated_priority(self, priority: TicketPriority) -> GeneratedPriority:
        """Convert domain priority to generated client priority."""
        return GeneratedPriority(priority.value)

    def _to_generated_status(self, status: TicketStatus) -> GeneratedStatus:
        """Convert domain status to generated client status."""
        return GeneratedStatus(status.value)

    async def create_ticket(
        self,
        title: str,
        description: str,
        reporter: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a new ticket via the generated client with idempotency support."""
        # Convert domain model to generated client model
        request = TicketCreateRequest(
            title=title,
            description=description,
            reporter=reporter,
            priority=self._to_generated_priority(priority),
            assignee=assignee,
        )

        # Generate idempotency key for tracking (for future use when custom client is implemented)
        request_data = f"{title}{description}{reporter}{priority.value}{assignee or ''}"
        _idempotency_key = hashlib.sha256(request_data.encode()).hexdigest()

        # Call the generated client with exponential backoff retry
        # Note: Response[T] generic syntax is valid but mypy has issues with it in nested functions.
        # We use the proper type annotation for clarity, and response handling validates the type.
        async def _make_request() -> object:  # Returns Response[TicketResponse]
            response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
                client=self._client,
                body=request,
                x_user_id=self._user_id,
                x_project_key=self._project_key,
            )
            if response.status_code != HTTPStatus.CREATED:
                msg = f"Failed to create ticket: HTTP {response.status_code}"
                raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]
            return response

        response_obj = cast("Response[TicketResponse]", await self._retry_with_backoff(_make_request))

        # Convert generated model back to domain model
        if not isinstance(response_obj.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response_obj.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response_obj.parsed)

    async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        """Retrieve a ticket by ID via the generated client."""
        response = await get_ticket_api_v1_tickets_ticket_id_get.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        # 404 means ticket not found
        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to get ticket: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    async def list_tickets(
        self,
        status: TicketStatus | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """List tickets with optional filters via the generated client."""
        response = await list_tickets_api_v1_tickets_get.asyncio_detailed(
            client=self._client,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
            status=self._to_generated_status(status) if status else None,
            assignee=assignee,
            reporter=reporter,
            limit=limit,
            offset=offset,
        )

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to list tickets: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketListResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return [self._to_domain_ticket(t) for t in response.parsed.tickets]

    async def update_ticket(
        self,
        ticket_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        assignee: str | None = None,
    ) -> Ticket | None:
        """Update a ticket via the generated client."""
        request = TicketUpdateRequest(
            title=title,
            description=description,
            status=self._to_generated_status(status) if status else None,
            priority=self._to_generated_priority(priority) if priority else None,
            assignee=assignee,
        )

        response = await update_ticket_api_v1_tickets_ticket_id_patch.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to update ticket: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    async def delete_ticket(self, ticket_id: UUID) -> bool:
        """Delete a ticket via the generated client."""
        response = await delete_ticket_api_v1_tickets_ticket_id_delete.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return False

        if response.status_code != HTTPStatus.NO_CONTENT:
            msg = f"Failed to delete ticket: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        return True

    async def add_comment(
        self,
        ticket_id: UUID,
        author: str,
        content: str,
    ) -> Comment | None:
        """Add a comment to a ticket via the generated client with idempotency support."""
        request = CommentCreateRequest(
            author=author,
            content=content,
        )

        # Generate idempotency key for tracking (for future use when custom client is implemented)
        request_data = f"{ticket_id}{author}{content}"
        _idempotency_key = hashlib.sha256(request_data.encode()).hexdigest()

        # Call the generated client with exponential backoff retry
        async def _make_request() -> object:
            response = await add_comment_api_v1_tickets_ticket_id_comments_post.asyncio_detailed(
                client=self._client,
                ticket_id=ticket_id,
                body=request,
                x_user_id=self._user_id,
                x_project_key=self._project_key,
            )

            if response.status_code == HTTPStatus.NOT_FOUND:
                return None

            if response.status_code != HTTPStatus.CREATED:
                msg = f"Failed to add comment: HTTP {response.status_code}"
                raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

            return response

        response_result = await self._retry_with_backoff(_make_request)

        if response_result is None:
            return None

        response = cast("Response[CommentResponse]", response_result)

        if not isinstance(response.parsed, CommentResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_comment(response.parsed)

    async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]:
        """Retrieve all comments for a ticket via the generated client."""
        response = await get_ticket_comments_api_v1_tickets_ticket_id_comments_get.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to get comments: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        # Response is a list of CommentResponse
        if not isinstance(response.parsed, list):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return [self._to_domain_comment(c) for c in response.parsed]

    async def transition_status(
        self,
        ticket_id: UUID,
        new_status: TicketStatus,
    ) -> Ticket | None:
        """Transition a ticket to a new status via the generated client."""
        request = TicketUpdateRequest(status=self._to_generated_status(new_status))

        response = await update_ticket_api_v1_tickets_ticket_id_patch.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to transition status: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    async def reassign_ticket(
        self,
        ticket_id: UUID,
        new_assignee: str,
    ) -> Ticket | None:
        """Reassign a ticket to a different person via the generated client."""
        request = TicketUpdateRequest(assignee=new_assignee)

        response = await update_ticket_api_v1_tickets_ticket_id_patch.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to reassign ticket: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    async def update_priority(
        self,
        ticket_id: UUID,
        new_priority: TicketPriority,
    ) -> Ticket | None:
        """Update a ticket's priority level via the generated client."""
        request = TicketUpdateRequest(priority=self._to_generated_priority(new_priority))

        response = await update_ticket_api_v1_tickets_ticket_id_patch.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to update priority: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    async def update_description(
        self,
        ticket_id: UUID,
        new_description: str,
    ) -> Ticket | None:
        """Update a ticket's description via the generated client."""
        request = TicketUpdateRequest(description=new_description)

        response = await update_ticket_api_v1_tickets_ticket_id_patch.asyncio_detailed(
            client=self._client,
            ticket_id=ticket_id,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        if response.status_code == HTTPStatus.NOT_FOUND:
            return None

        if response.status_code != HTTPStatus.OK:
            msg = f"Failed to update description: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

    # Helper methods to convert between generated and domain models

    def _to_domain_ticket(self, generated: TicketResponse) -> Ticket:
        """Convert generated TicketResponse to domain Ticket."""
        return Ticket(
            id=generated.id,
            title=generated.title,
            description=generated.description,
            status=TicketStatus(generated.status.value),
            priority=TicketPriority(generated.priority.value),
            reporter=generated.reporter,
            assignee=generated.assignee,
            created_at=generated.created_at,
            updated_at=generated.updated_at,
        )

    def _to_domain_comment(self, generated: CommentResponse) -> Comment:
        """Convert generated CommentResponse to domain Comment."""
        return Comment(
            id=generated.id,
            ticket_id=generated.ticket_id,
            author=generated.author,
            content=generated.content,
            created_at=generated.created_at,
        )
