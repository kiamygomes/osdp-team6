"""Remote HTTP client implementing TicketServiceAPI by wrapping the generated client."""

from http import HTTPStatus
from uuid import UUID

import httpx
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

from ticket_api import (
    Comment,
    Ticket,
    TicketPriority,
    TicketServiceAPI,
    TicketStatus,
)


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
    ) -> None:
        """Initialize the remote ticket service adapter.

        Args:
            base_url: Service base URL
            user_id: User identifier
            project_key: Jira project key

        """
        # Use the auto-generated client internally
        self._client = Client(base_url=base_url)
        self._user_id = user_id
        self._project_key = project_key

    async def __aenter__(self) -> "RemoteTicketService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        # Clean up the underlying HTTP client
        http_client = self._client.get_async_httpx_client()
        await http_client.aclose()

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
        """Create a new ticket via the generated client."""
        # Convert domain model to generated client model
        request = TicketCreateRequest(
            title=title,
            description=description,
            reporter=reporter,
            priority=self._to_generated_priority(priority),
            assignee=assignee,
        )

        # Call the generated client
        response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
            client=self._client,
            body=request,
            x_user_id=self._user_id,
            x_project_key=self._project_key,
        )

        # Check for errors
        if response.status_code != HTTPStatus.CREATED:
            msg = f"Failed to create ticket: HTTP {response.status_code}"
            raise httpx.HTTPStatusError(msg, request=None, response=None)  # type: ignore[arg-type]

        # Convert generated model back to domain model
        if not isinstance(response.parsed, TicketResponse):
            msg = f"Unexpected response type: {type(response.parsed)}"
            raise TypeError(msg)

        return self._to_domain_ticket(response.parsed)

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

    async def update_ticket(  # noqa: PLR0913
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
        """Add a comment to a ticket via the generated client."""
        request = CommentCreateRequest(
            author=author,
            content=content,
        )

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
