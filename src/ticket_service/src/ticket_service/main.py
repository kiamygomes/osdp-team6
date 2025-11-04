"""Main FastAPI application for the Ticket Service.

This service exposes the TicketImpl (from ticket_impl) over HTTP endpoints,
providing a REST API for ticket management operations.
"""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated, NamedTuple
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from ticket_api import TicketServiceAPI, TicketStatus
from ticket_impl import TicketImpl

# Import the actual OAuth functions from ticket_impl
from ticket_impl.oauth import build_authorize_url, exchange_code_for_tokens
from ticket_impl.storage import clear_user_tokens, get_user_tokens

from ticket_service.models import (
    CommentCreateRequest,
    CommentResponse,
    HealthResponse,
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
)

logger = logging.getLogger("ticket_service")

# ============================================================================
# APPLICATION SETUP
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    logger.info("Starting %s v%s", app.title, app.version)
    # Add database startup connections/shutdowns
    yield
    logger.info("Shutting down %s", app.title)


app = FastAPI(
    title="Ticket Service",
    description="REST API for ticket management backed by Jira",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store OAuth state tokens temporarily (in production, use Redis/database)
# Maps state -> user_id for the callback
_oauth_state_store: dict[str, str] = {}


# ============================================================================
# DEPENDENCIES
# ============================================================================


async def get_user_id(
    x_user_id: Annotated[str, Header(..., description="User ID for authentication")],
) -> str:
    """Extract user ID from X-User-ID header.

    The ticket_impl handles OAuth token storage per user_id.
    Clients should obtain user_id through the OAuth flow in ticket_impl.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-ID header",
        )

    # Allow test users to bypass OAuth for testing/development
    if x_user_id.startswith("test-"):
        return x_user_id

    # Verify user has valid OAuth tokens
    tokens = get_user_tokens(x_user_id)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated. Please complete OAuth flow at /api/v1/auth/login",
        )

    return x_user_id


async def get_project_key(
    x_project_key: Annotated[str, Header(..., description="Jira project key")],
) -> str:
    """Extract Jira project key from X-Project-Key header."""
    if not x_project_key:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Missing X-Project-Key header",
        )
    return x_project_key


async def get_ticket_service(
    user_id: Annotated[str, Depends(get_user_id)],
    project_key: Annotated[str, Depends(get_project_key)],
) -> TicketServiceAPI:
    """Provide the concrete TicketImpl instance.

    This dependency creates a TicketImpl configured for the authenticated user
    and their specified Jira project.
    """
    return TicketImpl(user_id=user_id, project_key=project_key)


# ============================================================================
# OAUTH 2.0 AUTHENTICATION ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/auth/login",
    tags=["authentication"],
    summary="Initiate OAuth 2.0 flow",
    response_class=RedirectResponse,
)
async def oauth_login() -> RedirectResponse:
    """Start the OAuth 2.0 authorization flow with Jira.

    This endpoint redirects the user to Jira's authorization page.
    After the user grants access, Jira will redirect back to the callback endpoint.
    """
    # Generate unique user_id and CSRF protection state
    user_id = str(uuid4())
    state = secrets.token_urlsafe(32)

    # Store mapping of state -> user_id for callback verification
    _oauth_state_store[state] = user_id

    # Get authorization URL from ticket_impl's oauth module
    auth_url = build_authorize_url(state=state)

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@app.get(
    "/api/v1/auth/callback",
    tags=["authentication"],
    summary="OAuth 2.0 callback endpoint",
)
async def oauth_callback(
    code: Annotated[str, Query(..., description="Authorization code from Jira")],
    state: Annotated[str, Query(..., description="State for CSRF protection")],
) -> dict[str, str]:
    """Handle the OAuth 2.0 callback from Jira.

    This endpoint receives the authorization code, exchanges it for tokens,
    and stores them for the user. Returns the user_id to use in subsequent requests.
    """
    # Verify state to prevent CSRF attacks
    if state not in _oauth_state_store:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )

    # Get the user_id associated with this state
    user_id = _oauth_state_store[state]

    # Remove state from store
    del _oauth_state_store[state]

    try:
        # Exchange code for tokens using ticket_impl's oauth module
        # This function stores the tokens internally
        await exchange_code_for_tokens(user_id=user_id, code=code)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {e!s}",
        ) from e
    else:
        return {
            "message": "Authentication successful",
            "user_id": user_id,
            "instructions": f"Use 'X-User-ID: {user_id}' header in subsequent API requests",
        }


@app.get(
    "/api/v1/auth/status",
    tags=["authentication"],
    summary="Check authentication status",
)
async def auth_status(
    user_id: Annotated[str, Query(..., description="User ID to check")],
) -> dict[str, bool | str]:
    """Check if a user has valid OAuth tokens stored.

    Returns whether the user is authenticated and when tokens expire.
    """
    tokens = get_user_tokens(user_id)

    if not tokens:
        return {
            "authenticated": False,
            "message": "User not authenticated. Please visit /api/v1/auth/login",
        }

    return {
        "authenticated": True,
        "user_id": user_id,
        "message": "User has valid tokens",
    }


@app.post(
    "/api/v1/auth/logout",
    tags=["authentication"],
    summary="Logout and revoke tokens",
    status_code=HTTPStatus.NO_CONTENT,
)
async def logout(
    user_id: Annotated[str, Query(..., description="User ID to logout")],
) -> None:
    """Logout the user by clearing their stored OAuth tokens.

    After logout, the user will need to complete the OAuth flow again.
    """
    clear_user_tokens(user_id)


# ============================================================================
# ROOT AND HEALTH CHECK ENDPOINTS
# ============================================================================


@app.get(
    "/",
    tags=["info"],
    summary="Service information",
)
async def root() -> dict[str, str]:
    """Root endpoint providing basic service information and navigation."""
    return {
        "service": "OSDP Jira Service",
        "version": "0.1.0",
        "description": "REST API for ticket management backed by Jira",
        "docs": "/docs",
        "health": "/health",
        "openapi": "/api/v1/openapi.json",
        "oauth_login": "/api/v1/auth/login",
    }


@app.get(
    "/favicon.ico",
    include_in_schema=False,
)
async def favicon() -> Response:
    """Return empty favicon to prevent 404 errors."""
    return Response(status_code=204)


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Verify that the service is running and responsive."""
    return HealthResponse(
        status="healthy",
        service="ticket_service",
        version="0.1.0",
    )


# ============================================================================
# TICKET ENDPOINTS
# ============================================================================


@app.post(
    "/api/v1/tickets",
    status_code=status.HTTP_201_CREATED,
    tags=["tickets"],
    summary="Create a new ticket",
)
async def create_ticket(
    request: TicketCreateRequest,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> TicketResponse:
    """Create a new ticket in Jira.

    Requires X-User-ID and X-Project-Key headers.
    """
    try:
        ticket = await service.create_ticket(
            title=request.title,
            description=request.description,
            reporter=request.reporter,
            priority=request.priority,
            assignee=request.assignee,
        )
        return TicketResponse.model_validate(ticket)
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {e!s}",
        ) from e


@app.get(
    "/api/v1/tickets/{ticket_id}",
    tags=["tickets"],
    summary="Get a ticket by ID",
)
async def get_ticket(
    ticket_id: UUID,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> TicketResponse:
    """Retrieve a specific ticket by its UUID.

    Returns 404 if the ticket is not found.
    """
    ticket = await service.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return TicketResponse.model_validate(ticket)


class TicketFilters(NamedTuple):
    """Grouped ticket filtering parameters."""

    status: TicketStatus | None
    assignee: str | None
    reporter: str | None


async def get_ticket_filters(
    status_filter: Annotated[
        TicketStatus | None,
        Query(alias="status", description="Filter by ticket status"),
    ] = None,
    assignee: Annotated[
        str | None,
        Query(description="Filter by assignee username/email"),
    ] = None,
    reporter: Annotated[
        str | None,
        Query(description="Filter by reporter username/email"),
    ] = None,
) -> TicketFilters:
    """Dependency that groups ticket filtering parameters into a single object."""
    return TicketFilters(status=status_filter, assignee=assignee, reporter=reporter)


@app.get(
    "/api/v1/tickets",
    tags=["tickets"],
    summary="List tickets with filtering",
)
async def list_tickets(
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
    filters: Annotated[TicketFilters, Depends(get_ticket_filters)],
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of tickets to return"),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of tickets to skip"),
    ] = 0,
) -> TicketListResponse:
    """List tickets with optional filtering and pagination.

    All filter parameters are optional. Results are paginated using limit/offset.
    """
    try:
        tickets = await service.list_tickets(
            status=filters.status,
            assignee=filters.assignee,
            reporter=filters.reporter,
            limit=limit,
            offset=offset,
        )

        ticket_responses = [TicketResponse.model_validate(t) for t in tickets]

        return TicketListResponse(
            tickets=ticket_responses,
            total=len(ticket_responses),
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tickets: {e!s}",
        ) from e


@app.patch(
    "/api/v1/tickets/{ticket_id}",
    tags=["tickets"],
    summary="Update a ticket",
)
async def update_ticket(
    ticket_id: UUID,
    request: TicketUpdateRequest,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> TicketResponse:
    """Update an existing ticket. All fields are optional - only provided fields will be updated.

    Returns 404 if the ticket is not found.
    """
    try:
        ticket = await service.update_ticket(
            ticket_id=ticket_id,
            title=request.title,
            description=request.description,
            status=request.status,
            priority=request.priority,
            assignee=request.assignee,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ticket: {e!s}",
        ) from e
    if ticket is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return TicketResponse.model_validate(ticket)


@app.delete(
    "/api/v1/tickets/{ticket_id}",
    status_code=HTTPStatus.NO_CONTENT,
    tags=["tickets"],
    summary="Delete a ticket",
)
async def delete_ticket(
    ticket_id: UUID,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> None:
    """Delete a ticket permanently.

    Returns 404 if the ticket is not found.
    """
    success = await service.delete_ticket(ticket_id)
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )


# ============================================================================
# COMMENT ENDPOINTS
# ============================================================================


@app.post(
    "/api/v1/tickets/{ticket_id}/comments",
    status_code=status.HTTP_201_CREATED,
    tags=["comments"],
    summary="Add a comment to a ticket",
)
async def add_comment(
    ticket_id: UUID,
    request: CommentCreateRequest,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> CommentResponse:
    """Add a new comment to an existing ticket.

    Returns 404 if the ticket is not found.
    """
    try:
        comment = await service.add_comment(
            ticket_id=ticket_id,
            author=request.author,
            content=request.content,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {e!s}",
        ) from e
    if comment is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return CommentResponse.model_validate(comment)


@app.get(
    "/api/v1/tickets/{ticket_id}/comments",
    tags=["comments"],
    summary="Get all comments for a ticket",
)
async def get_ticket_comments(
    ticket_id: UUID,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)],
) -> list[CommentResponse]:
    """Retrieve all comments for a specific ticket.

    Returns an empty list if the ticket has no comments or is not found.
    """
    comments = await service.get_ticket_comments(ticket_id)
    return [CommentResponse.model_validate(c) for c in comments]
