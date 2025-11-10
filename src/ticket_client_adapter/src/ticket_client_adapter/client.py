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
import contextlib
import hashlib
import logging
import secrets
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, TypeVar, cast
from uuid import UUID, uuid4

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

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    Opens after a threshold of consecutive failures, preventing further requests.
    After a timeout, enters half-open state to test if service has recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = httpx.HTTPError,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track for failures

        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED

    def record_success(self) -> None:
        """Record a successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker opened after %s consecutive failures",
                self.failure_count,
            )

    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time is not None and (time.time() - self.last_failure_time >= self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        return True

    async def call(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Execute operation with circuit breaker protection."""
        if not self.can_attempt():
            msg = "Circuit breaker is open"
            raise httpx.HTTPError(msg)

        try:
            result = await operation()
        except self.expected_exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result


class IdempotentClient(Client):
    """Extended Client that supports idempotency headers.

    Wraps the auto-generated Client to add Idempotency-Key header support
    for safe retries on idempotent operations.
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """Initialize the idempotent client.

        Args:
            base_url: Base URL for the service
            timeout: Request timeout in seconds

        """
        super().__init__(base_url=base_url, timeout=httpx.Timeout(timeout))
        self._idempotency_key: str | None = None
        self._correlation_id: str | None = None
        self._httpx_client: httpx.AsyncClient | None = None

    def set_idempotency_key(self, key: str) -> None:
        """Set the current idempotency key for the next request."""
        self._idempotency_key = key
        self._reset_client()

    def clear_idempotency_key(self) -> None:
        """Clear the idempotency key after request."""
        self._idempotency_key = None
        self._reset_client()

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for tracking requests."""
        self._correlation_id = correlation_id
        self._reset_client()

    def clear_correlation_id(self) -> None:
        """Clear the correlation ID."""
        self._correlation_id = None
        self._reset_client()

    def _reset_client(self) -> None:
        """Reset the httpx client to pick up new headers."""
        if self._httpx_client is not None:
            self._httpx_client = None

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        """Get the async httpx client with custom headers and timeout."""
        if self._httpx_client is None:
            headers: dict[str, str] = {}
            if self._idempotency_key is not None:
                headers["Idempotency-Key"] = self._idempotency_key
            if self._correlation_id is not None:
                headers["X-Correlation-ID"] = self._correlation_id

            self._httpx_client = httpx.AsyncClient(
                headers=headers,
                timeout=self._timeout,
                base_url=self._base_url,
            )
        return self._httpx_client

    async def aclose(self) -> None:
        """Close the httpx client."""
        if self._httpx_client is not None:
            await self._httpx_client.aclose()
            self._httpx_client = None


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
        timeout: float = 30.0,
    ) -> None:
        """Initialize the remote ticket service adapter.

        Args:
            base_url: Service base URL
            user_id: User identifier
            project_key: Jira project key
            max_retries: Maximum number of retry attempts for transient failures
            initial_backoff_seconds: Initial backoff duration in seconds for exponential backoff
            timeout: Request timeout in seconds

        """
        self._client = IdempotentClient(base_url=base_url, timeout=timeout)
        self._user_id = user_id
        self._project_key = project_key
        self._max_retries = max_retries
        self._initial_backoff_seconds = initial_backoff_seconds
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )

    async def __aenter__(self) -> "RemoteTicketService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self._client.aclose()

    def _calculate_backoff_with_jitter(self, attempt: int, retry_after: float | None = None) -> float:
        """Calculate backoff time with exponential backoff and jitter.

        Args:
            attempt: Current retry attempt number (0-indexed)
            retry_after: Optional Retry-After header value in seconds

        Returns:
            Backoff duration in seconds

        """
        if retry_after is not None:
            return retry_after

        base_backoff: float = self._initial_backoff_seconds * (2**attempt)
        jitter_ms: int = secrets.randbelow(1000)
        return base_backoff + float(jitter_ms) / 1000.0

    async def _retry_with_backoff(
        self,
        operation: Callable[[], Awaitable[object]],
        correlation_id: str,
    ) -> object:
        """Execute operation with exponential backoff retry on transient failures.

        Args:
            operation: Async callable to execute with no arguments
            correlation_id: Correlation ID for tracking this request

        Returns:
            Result from the operation

        Raises:
            httpx.HTTPError: If all retries are exhausted

        """
        last_exception: httpx.HTTPStatusError | httpx.ConnectError | httpx.TimeoutException | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._circuit_breaker.call(operation)
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response is not None and (
                    e.response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
                    and e.response.status_code != HTTPStatus.TOO_MANY_REQUESTS
                ):
                    logger.exception(
                        "Client error for correlation_id=%s: HTTP %s",
                        correlation_id,
                        e.response.status_code,
                    )
                    raise

                if attempt < self._max_retries - 1:
                    retry_after = None
                    if e.response is not None and "Retry-After" in e.response.headers:
                        with contextlib.suppress(ValueError):
                            retry_after = float(e.response.headers["Retry-After"])

                    backoff_seconds = self._calculate_backoff_with_jitter(attempt, retry_after)
                    logger.warning(
                        "Retry attempt %s for correlation_id=%s after %s seconds (HTTP %s)",
                        attempt + 1,
                        correlation_id,
                        backoff_seconds,
                        e.response.status_code if e.response else "unknown",
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.exception(
                        "All retries exhausted for correlation_id=%s",
                        correlation_id,
                    )
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    backoff_seconds = self._calculate_backoff_with_jitter(attempt)
                    logger.warning(
                        "Network error on attempt %s for correlation_id=%s, retrying after %s seconds",
                        attempt + 1,
                        correlation_id,
                        backoff_seconds,
                        exc_info=True,
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.exception(
                        "All retries exhausted for correlation_id=%s due to network error",
                        correlation_id,
                    )

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
        correlation_id = str(uuid4())
        request_data = "{}{}{}{}{}".format(title, description, reporter, priority.value, assignee or "")
        idempotency_key = hashlib.sha256(request_data.encode()).hexdigest()

        logger.info(
            "Creating ticket with correlation_id=%s, idempotency_key=%s",
            correlation_id,
            idempotency_key,
        )

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:
            request = TicketCreateRequest(
                title=title,
                description=description,
                reporter=reporter,
                priority=self._to_generated_priority(priority),
                assignee=assignee,
            )

            async def _make_request() -> object:
                response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
                    client=self._client,
                    body=request,
                    x_user_id=self._user_id,
                    x_project_key=self._project_key,
                )
                if response.status_code != HTTPStatus.CREATED:
                    msg = f"Failed to create ticket: HTTP {response.status_code}"
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_obj = cast(
                "Response[TicketResponse]",
                await self._retry_with_backoff(_make_request, correlation_id),
            )

            if not isinstance(response_obj.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response_obj.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully created ticket with correlation_id=%s, ticket_id=%s",
                correlation_id,
                response_obj.parsed.id,
            )
            return self._to_domain_ticket(response_obj.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        """Retrieve a ticket by ID via the generated client with retry support."""
        correlation_id = str(uuid4())
        logger.info(
            "Getting ticket with correlation_id=%s, ticket_id=%s",
            correlation_id,
            ticket_id,
        )

        async def _make_request() -> object:
            response = await get_ticket_api_v1_tickets_ticket_id_get.asyncio_detailed(
                client=self._client,
                ticket_id=ticket_id,
                x_user_id=self._user_id,
                x_project_key=self._project_key,
            )

            # 404 means ticket not found - don't retry
            if response.status_code == HTTPStatus.NOT_FOUND:
                return None

            if response.status_code != HTTPStatus.OK:
                msg = f"Failed to get ticket: HTTP {response.status_code}"
                req = cast("httpx.Request", response)
                resp = cast("httpx.Response", response)
                raise httpx.HTTPStatusError(msg, request=req, response=resp)
            return response

        response_result = await self._retry_with_backoff(_make_request, correlation_id)

        if response_result is None:
            logger.info(
                "Ticket not found for correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return None

        response = cast("Response[TicketResponse]", response_result)
        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        logger.info(
            "Successfully retrieved ticket with correlation_id=%s, ticket_id=%s",
            correlation_id,
            ticket_id,
        )
        return self._to_domain_ticket(response.parsed)

    async def list_tickets(
        self,
        status: TicketStatus | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """List tickets with optional filters via the generated client with retry support."""
        correlation_id = str(uuid4())
        logger.info(
            "Listing tickets with correlation_id=%s, status=%s, assignee=%s, reporter=%s",
            correlation_id,
            status,
            assignee,
            reporter,
        )

        async def _make_request() -> object:
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
                req = cast("httpx.Request", response)
                resp = cast("httpx.Response", response)
                raise httpx.HTTPStatusError(msg, request=req, response=resp)
            return response

        response = cast(
            "Response[TicketListResponse]",
            await self._retry_with_backoff(_make_request, correlation_id),
        )

        if not isinstance(response.parsed, TicketListResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        logger.info(
            "Successfully listed tickets with correlation_id=%s, count=%s",
            correlation_id,
            len(response.parsed.tickets),
        )
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
        """Update a ticket via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # Generate idempotency key from ticket ID and update fields
        request_data = f"update_{ticket_id}_{title}_{description}_{status}_{priority}_{assignee}"
        idempotency_key = hashlib.sha256(request_data.encode()).hexdigest()

        logger.info(
            "Updating ticket with correlation_id=%s, idempotency_key=%s, ticket_id=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
        )

        request = TicketUpdateRequest(
            title=title,
            description=description,
            status=self._to_generated_status(status) if status else None,
            priority=self._to_generated_priority(priority) if priority else None,
            assignee=assignee,
        )

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[TicketResponse]", response_result)
            if not isinstance(response.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully updated ticket with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return self._to_domain_ticket(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def delete_ticket(self, ticket_id: UUID) -> bool:
        """Delete a ticket via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # DELETE is idempotent - same idempotency key for multiple attempts
        idempotency_key = hashlib.sha256(f"delete_{ticket_id}".encode()).hexdigest()

        logger.info(
            "Deleting ticket with correlation_id=%s, idempotency_key=%s, ticket_id=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
        )

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
                response = await delete_ticket_api_v1_tickets_ticket_id_delete.asyncio_detailed(
                    client=self._client,
                    ticket_id=ticket_id,
                    x_user_id=self._user_id,
                    x_project_key=self._project_key,
                )

                if response.status_code == HTTPStatus.NOT_FOUND:
                    return None

                if response.status_code != HTTPStatus.NO_CONTENT:
                    msg = f"Failed to delete ticket: HTTP {response.status_code}"
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return False

            logger.info(
                "Successfully deleted ticket with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return True
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def add_comment(
        self,
        ticket_id: UUID,
        author: str,
        content: str,
    ) -> Comment | None:
        """Add a comment to a ticket via the generated client with idempotency support."""
        correlation_id = str(uuid4())
        request_data = f"{ticket_id}{author}{content}"
        idempotency_key = hashlib.sha256(request_data.encode()).hexdigest()

        logger.info(
            "Adding comment with correlation_id=%s, idempotency_key=%s, ticket_id=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
        )

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:
            request = CommentCreateRequest(
                author=author,
                content=content,
            )

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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)

                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[CommentResponse]", response_result)

            if not isinstance(response.parsed, CommentResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully added comment with correlation_id=%s, comment_id=%s",
                correlation_id,
                response.parsed.id,
            )
            return self._to_domain_comment(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]:
        """Retrieve all comments for a ticket via the generated client with retry support."""
        correlation_id = str(uuid4())
        logger.info(
            "Getting ticket comments with correlation_id=%s, ticket_id=%s",
            correlation_id,
            ticket_id,
        )

        async def _make_request() -> object:
            response = await get_ticket_comments_api_v1_tickets_ticket_id_comments_get.asyncio_detailed(
                client=self._client,
                ticket_id=ticket_id,
                x_user_id=self._user_id,
                x_project_key=self._project_key,
            )

            if response.status_code != HTTPStatus.OK:
                msg = f"Failed to get comments: HTTP {response.status_code}"
                req = cast("httpx.Request", response)
                resp = cast("httpx.Response", response)
                raise httpx.HTTPStatusError(msg, request=req, response=resp)
            return response

        response = cast(
            "Response[list[CommentResponse]]",
            await self._retry_with_backoff(_make_request, correlation_id),
        )

        # Response is a list of CommentResponse
        if not isinstance(response.parsed, list):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        logger.info(
            "Successfully retrieved ticket comments with correlation_id=%s, ticket_id=%s, count=%s",
            correlation_id,
            ticket_id,
            len(response.parsed),
        )
        return [self._to_domain_comment(c) for c in response.parsed]

    async def transition_status(
        self,
        ticket_id: UUID,
        new_status: TicketStatus,
    ) -> Ticket | None:
        """Transition a ticket to a new status via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # Generate idempotency key from ticket ID and new status
        idempotency_key = hashlib.sha256(
            f"transition_{ticket_id}_{new_status.value}".encode(),
        ).hexdigest()

        logger.info(
            "Transitioning ticket status with correlation_id=%s, idempotency_key=%s, ticket_id=%s, new_status=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
            new_status,
        )

        request = TicketUpdateRequest(status=self._to_generated_status(new_status))

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[TicketResponse]", response_result)
            if not isinstance(response.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully transitioned ticket status with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return self._to_domain_ticket(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def reassign_ticket(
        self,
        ticket_id: UUID,
        new_assignee: str,
    ) -> Ticket | None:
        """Reassign a ticket to a different person via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # Generate idempotency key from ticket ID and new assignee
        idempotency_key = hashlib.sha256(
            f"reassign_{ticket_id}_{new_assignee}".encode(),
        ).hexdigest()

        logger.info(
            "Reassigning ticket with correlation_id=%s, idempotency_key=%s, ticket_id=%s, new_assignee=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
            new_assignee,
        )

        request = TicketUpdateRequest(assignee=new_assignee)

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[TicketResponse]", response_result)
            if not isinstance(response.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully reassigned ticket with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return self._to_domain_ticket(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def update_priority(
        self,
        ticket_id: UUID,
        new_priority: TicketPriority,
    ) -> Ticket | None:
        """Update a ticket's priority level via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # Generate idempotency key from ticket ID and new priority
        idempotency_key = hashlib.sha256(
            f"priority_{ticket_id}_{new_priority.value}".encode(),
        ).hexdigest()

        logger.info(
            "Updating ticket priority with correlation_id=%s, idempotency_key=%s, ticket_id=%s, new_priority=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
            new_priority,
        )

        request = TicketUpdateRequest(priority=self._to_generated_priority(new_priority))

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[TicketResponse]", response_result)
            if not isinstance(response.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully updated ticket priority with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return self._to_domain_ticket(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

    async def update_description(
        self,
        ticket_id: UUID,
        new_description: str,
    ) -> Ticket | None:
        """Update a ticket's description via the generated client with retry and idempotency support."""
        correlation_id = str(uuid4())
        # Generate idempotency key from ticket ID and new description
        idempotency_key = hashlib.sha256(
            f"description_{ticket_id}_{new_description}".encode(),
        ).hexdigest()

        logger.info(
            "Updating ticket description with correlation_id=%s, idempotency_key=%s, ticket_id=%s",
            correlation_id,
            idempotency_key,
            ticket_id,
        )

        request = TicketUpdateRequest(description=new_description)

        self._client.set_idempotency_key(idempotency_key)
        self._client.set_correlation_id(correlation_id)

        try:

            async def _make_request() -> object:
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
                    req = cast("httpx.Request", response)
                    resp = cast("httpx.Response", response)
                    raise httpx.HTTPStatusError(msg, request=req, response=resp)
                return response

            response_result = await self._retry_with_backoff(_make_request, correlation_id)

            if response_result is None:
                logger.info(
                    "Ticket not found for correlation_id=%s, ticket_id=%s",
                    correlation_id,
                    ticket_id,
                )
                return None

            response = cast("Response[TicketResponse]", response_result)
            if not isinstance(response.parsed, TicketResponse):
                msg = f"Unexpected response type: {type(response.parsed)}"
                raise TypeError(msg)

            logger.info(
                "Successfully updated ticket description with correlation_id=%s, ticket_id=%s",
                correlation_id,
                ticket_id,
            )
            return self._to_domain_ticket(response.parsed)
        finally:
            self._client.clear_idempotency_key()
            self._client.clear_correlation_id()

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
