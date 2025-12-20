"""FastAPI Web Service for the Main Orchestrator Application.

This service exposes the 3-vertical integration (Chat → AI → Tickets) via HTTP endpoints
for deployment to Render or other cloud platforms.

Endpoints:
- POST /process - Process a natural language command through the full pipeline
- POST /process-chat - Process a chat message with channel context
- GET /health - Health check endpoint
- GET /status - Service status and configuration
"""

from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from ticket_impl.oauth import build_authorize_url, exchange_code_for_tokens
from ticket_impl.storage import get_tokens, is_expired

from orchestrator.main_app import TicketBotOrchestrator

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# Try to import optional AI providers
try:
    import ai_api  # type: ignore[import-not-found]
except ImportError:
    ai_api = None  # type: ignore[assignment]

try:
    import ai_chat_api  # type: ignore[import-not-found]
except ImportError:
    ai_chat_api = None  # type: ignore[assignment]

try:
    import chat_api.chat_api  # type: ignore[import-not-found]
except ImportError:
    chat_api = None  # type: ignore[assignment,misc]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# In-memory OAuth state storage (use Redis in production)
_oauth_state_store: dict[str, str] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def check_ai_providers() -> dict[str, bool]:
    """Check which AI providers are available.

    Returns:
        Dictionary mapping provider names to availability status.

    """
    providers: dict[str, bool] = {"claude": False, "openai": False}

    if ai_chat_api is not None:
        try:
            ai_chat_api.get_ai_interface()
            providers["claude"] = True
        except (AttributeError, RuntimeError) as e:
            logger.debug("Claude AI provider not available: %s", e)

    if ai_api is not None:
        try:
            ai_api.get_client()
            providers["openai"] = True
        except (AttributeError, RuntimeError) as e:
            logger.debug("OpenAI AI provider not available: %s", e)

    return providers


def check_chat_available() -> bool:
    """Check if chat interface is available.

    Returns:
        True if chat interface is available, False otherwise.

    """
    if chat_api is None:
        return False

    try:
        return hasattr(chat_api.chat_api, "ChatInterface")
    except AttributeError as e:
        logger.debug("Chat interface not available: %s", e)
        return False


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup and shutdown events.

    Args:
        _app: FastAPI application instance (unused but required by signature).

    Yields:
        None during application lifetime.

    """
    # Startup
    logger.info("Starting OSDP Ticket Bot Orchestrator Service")
    logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))

    # Log available AI providers
    providers = check_ai_providers()
    if providers["claude"]:
        logger.info("Claude AI provider available")
    else:
        logger.warning("Claude AI provider not available")

    if providers["openai"]:
        logger.info("OpenAI AI provider available")
    else:
        logger.warning("OpenAI AI provider not available")

    logger.info("Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down OSDP Ticket Bot Orchestrator Service")


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="OSDP Ticket Bot Orchestrator",
    description="3-Vertical Integration: Chat → AI → Tickets",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ProcessCommandRequest(BaseModel):
    """Request model for processing a command."""

    message: str = Field(..., description="Natural language command to process")
    user_id: str = Field(default="demo_user", description="User ID for ticket operations")
    project_key: str = Field(default="DEMO", description="Jira project key")
    ai_provider: str = Field(
        default="claude",
        description="AI provider to use ('claude' or 'openai')",
    )


class ProcessChatRequest(BaseModel):
    """Request model for processing a chat message."""

    message: str = Field(..., description="Natural language command to process")
    channel_id: str = Field(..., description="Chat channel ID")
    user_id: str = Field(default="demo_user", description="User ID for ticket operations")
    project_key: str = Field(default="DEMO", description="Jira project key")
    ai_provider: str = Field(
        default="claude",
        description="AI provider to use ('claude' or 'openai')",
    )


class CommandResponse(BaseModel):
    """Response model for command processing."""

    success: bool
    message: str
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: str | None = None
    ai_provider: str
    user_id: str
    project_key: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str


class StatusResponse(BaseModel):
    """Service status response."""

    service: str
    version: str
    environment: str
    ai_provider_available: dict[str, bool]
    chat_available: bool
    ticket_service_available: bool


class AuthStatusResponse(BaseModel):
    """Authentication status response."""

    authenticated: bool
    user_id: str
    has_valid_tokens: bool
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": "OSDP Ticket Bot Orchestrator",
        "version": "1.0.0",
        "description": "3-Vertical Integration: Chat → AI → Tickets",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        service="ticket-bot-orchestrator",
        version="1.0.0",
    )


@app.get("/status", response_model=StatusResponse)
async def service_status() -> StatusResponse:
    """Get detailed service status and configuration."""
    return StatusResponse(
        service="ticket-bot-orchestrator",
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        ai_provider_available=check_ai_providers(),
        chat_available=check_chat_available(),
        ticket_service_available=True,  # Always true if service is running
    )


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@app.get("/auth/login")
async def auth_login(user_id: str = "demo_user") -> dict[str, str]:
    """Initiate OAuth 2.0 flow for Jira authentication.

    This endpoint starts the OAuth flow for users to authenticate with Jira.
    After visiting the auth_url, users will be redirected to /auth/callback.

    Args:
        user_id: User identifier (defaults to "demo_user")

    Returns:
        Dictionary with authorization URL and instructions

    Example:
        GET /auth/login?user_id=alice
        Response: {
            "auth_url": "https://auth.atlassian.com/authorize?...",
            "message": "Please visit the auth_url to authorize",
            "user_id": "alice"
        }

    """
    logger.info("Starting Jira OAuth flow for user=%s", user_id)

    # Check if user already has valid Jira tokens
    tokens = get_tokens(user_id, service_name="jira")
    if tokens and not is_expired(tokens):
        logger.info("User %s already has valid Jira tokens", user_id)
        return {
            "message": "Already authenticated with Jira",
            "user_id": user_id,
            "authenticated": "true",
        }

    # Generate state parameter and store user_id mapping
    state = secrets.token_urlsafe(32)
    _oauth_state_store[state] = user_id
    logger.info("Generated OAuth state for user=%s", user_id)

    # Build Jira authorization URL
    auth_url = build_authorize_url(state)
    logger.info("Jira authorization URL: %s", auth_url)

    return {
        "auth_url": auth_url,
        "message": "Please visit the auth_url to authorize with Jira",
        "user_id": user_id,
        "service": "jira",
    }


@app.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(code: str, state: str) -> HTMLResponse:
    """OAuth 2.0 callback endpoint for Jira.

    This endpoint receives the authorization code from Jira after the user
    authorizes the application. It exchanges the code for access tokens.

    Args:
        code: Authorization code from Jira OAuth provider
        state: State parameter to prevent CSRF attacks

    Returns:
        HTML page showing success or error message

    Raises:
        HTTPException: If state is invalid or token exchange fails

    """
    logger.info("Received Jira OAuth callback with state=%s", state)

    # Validate state parameter
    if state not in _oauth_state_store:
        logger.error("Invalid OAuth state: %s", state)
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                    .error { background-color: #fee; border: 1px solid #fcc; border-radius: 5px; padding: 20px; }
                    h1 { color: #c00; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Authentication Failed</h1>
                    <p>Invalid state parameter. This could be a security issue.</p>
                    <p>Please try authenticating again by visiting <a href="/auth/login">/auth/login</a></p>
                </div>
            </body>
            </html>
            """,
            status_code=400,
        )

    # Get user_id and remove state from store
    user_id = _oauth_state_store.pop(state)
    logger.info("Processing Jira OAuth callback for user=%s", user_id)

    try:
        # Exchange code for tokens (this stores them automatically)
        _access_token, _refresh_token, _expires_in = await exchange_code_for_tokens(
            user_id, code
        )
    except Exception as e:
        logger.exception("Failed to exchange code for Jira tokens")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                    .error {{ background-color: #fee; border: 1px solid #fcc; border-radius: 5px; padding: 20px; }}
                    h1 {{ color: #c00; }}
                    pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Authentication Failed</h1>
                    <p>Failed to exchange authorization code for tokens.</p>
                    <p><strong>Error:</strong></p>
                    <pre>{e!s}</pre>
                    <p>Please try again by visiting <a href="/auth/login?user_id={user_id}">/auth/login</a></p>
                </div>
            </body>
            </html>
            """,
            status_code=500,
        )
    else:
        logger.info("Successfully exchanged code for Jira tokens (user=%s)", user_id)

        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                    .success {{ background-color: #efe; border: 1px solid #cfc; border-radius: 5px; padding: 20px; }}
                    h1 {{ color: #090; }}
                    .info {{ background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    code {{ background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <div class="success">
                    <h1>✅ Authentication Successful!</h1>
                    <p>You have successfully authenticated with Jira.</p>
                    <div class="info">
                        <p><strong>User ID:</strong> <code>{user_id}</code></p>
                        <p><strong>Service:</strong> Jira</p>
                        <p><strong>Status:</strong> Ready to use</p>
                    </div>
                    <p>You can now:</p>
                    <ul>
                        <li>Use the orchestrator to create and manage tickets</li>
                        <li>Check your <a href="/auth/status?user_id={user_id}">authentication status</a></li>
                        <li>View the <a href="/docs">API documentation</a></li>
                    </ul>
                    <p style="margin-top: 20px; color: #666;">You can close this window now.</p>
                </div>
            </body>
            </html>
            """,
        )


@app.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status(user_id: str = "demo_user") -> AuthStatusResponse:
    """Check Jira authentication status for a user.

    Args:
        user_id: User identifier to check

    Returns:
        Authentication status information

    """
    tokens = get_tokens(user_id, service_name="jira")

    if not tokens:
        return AuthStatusResponse(
            authenticated=False,
            user_id=user_id,
            has_valid_tokens=False,
            message=f"User '{user_id}' has not authenticated with Jira yet. Visit /auth/login to authenticate.",
        )

    if is_expired(tokens):
        return AuthStatusResponse(
            authenticated=False,
            user_id=user_id,
            has_valid_tokens=False,
            message=f"User '{user_id}' Jira tokens are expired. Visit /auth/login to re-authenticate.",
        )

    return AuthStatusResponse(
        authenticated=True,
        user_id=user_id,
        has_valid_tokens=True,
        message=f"User '{user_id}' is authenticated with Jira and ready to use the orchestrator.",
    )


# ============================================================================
# COMMAND PROCESSING ENDPOINTS
# ============================================================================


@app.post("/process", response_model=CommandResponse)
async def process_command(request: ProcessCommandRequest) -> CommandResponse:
    """Process a natural language command through the full pipeline.

    This endpoint demonstrates the complete 3-vertical integration:
    1. Receives natural language input
    2. Routes to AI service for interpretation
    3. Executes ticket operations
    4. Returns structured response

    Example:
        POST /process
        {
            "message": "Create a ticket for fixing the login bug with high priority",
            "user_id": "demo_user",
            "project_key": "DEMO",
            "ai_provider": "claude"
        }

    Args:
        request: Command processing request with message and configuration.

    Returns:
        CommandResponse with success status and results.

    Raises:
        HTTPException: If validation or processing fails.

    """
    logger.info(
        "Processing command: %s (user=%s, project=%s, ai=%s)",
        request.message,
        request.user_id,
        request.project_key,
        request.ai_provider,
    )

    try:
        # Create orchestrator with specified configuration
        orchestrator = TicketBotOrchestrator(
            user_id=request.user_id,
            project_key=request.project_key,
            ai_provider=request.ai_provider,
        )

        # Process the command
        result = await orchestrator.process_chat_message(request.message)

        # Return response
        return CommandResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data"),
            error=result.get("error"),
            ai_provider=request.ai_provider,
            user_id=request.user_id,
            project_key=request.project_key,
        )

    except ValueError as e:
        # Handle validation errors
        logger.exception("Validation error processing command")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except RuntimeError as e:
        # Handle runtime errors (e.g., AI provider not available)
        logger.exception("Runtime error processing command")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e!s}",
        ) from e


@app.post("/process-chat", response_model=CommandResponse)
async def process_chat_message(request: ProcessChatRequest) -> CommandResponse:
    """Process a chat message with channel context.

    This endpoint includes chat channel information for bidirectional
    Chat ↔ AI ↔ Tickets integration.

    Example:
        POST /process-chat
        {
            "message": "List all open tickets",
            "channel_id": "general",
            "user_id": "demo_user",
            "project_key": "DEMO",
            "ai_provider": "openai"
        }

    Args:
        request: Chat message processing request with channel context.

    Returns:
        CommandResponse with success status and results.

    Raises:
        HTTPException: If validation or processing fails.

    """
    logger.info(
        "Processing chat message: %s (channel=%s, user=%s, ai=%s)",
        request.message,
        request.channel_id,
        request.user_id,
        request.ai_provider,
    )

    try:
        # Create orchestrator
        orchestrator = TicketBotOrchestrator(
            user_id=request.user_id,
            project_key=request.project_key,
            ai_provider=request.ai_provider,
        )

        # Process with channel context
        result = await orchestrator.process_chat_message(
            message=request.message,
            channel_id=request.channel_id,
        )

        return CommandResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data"),
            error=result.get("error"),
            ai_provider=request.ai_provider,
            user_id=request.user_id,
            project_key=request.project_key,
        )

    except ValueError as e:
        logger.exception("Validation error processing chat message")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except RuntimeError as e:
        logger.exception("Runtime error processing chat message")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {e!s}",
        ) from e


if __name__ == "__main__":
    import uvicorn

    # For local development only
    # In production, Render will start the app directly
    uvicorn.run(
        "orchestrator.orchestrator_service:app",
        host="127.0.0.1",  # Localhost only for development
        port=int(os.getenv("PORT", "8080")),
        log_level="info",
        reload=True,
    )
