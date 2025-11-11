"""Demo script for the Jira ticket service with OAuth 2.0 authentication.

This script demonstrates:
1. OAuth 2.0 authentication with Atlassian
2. Token storage and retrieval
3. All ticket service operations (CRUD operations on tickets)
"""

import asyncio
import logging
import os
import re
import sys
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticket_api.models import TicketPriority, TicketStatus
from ticket_impl.impl import TicketImpl
from ticket_impl.oauth import (
    build_authorize_url,
    exchange_code_for_tokens,
    fetch_cloud_id_from_api,
    fetch_project_key_from_api,
)
from ticket_impl.storage import get_tokens, is_expired

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Suppress verbose httpx and httpcore debug logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Constants
HTTP_PORT = 8000
HTTP_PORT_FALLBACK = 8001
CALLBACK_TIMEOUT = 300.0
HTTP_200 = 200
HTTP_400 = 400


async def start_callback_server(port: int = HTTP_PORT) -> str:
    """Start a local HTTP server to capture OAuth callback.

    Returns:
        The authorization code from the callback

    """
    auth_code_holder: dict[str, str] = {}
    done_event = asyncio.Event()

    async def handle_callback(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle the OAuth callback request."""
        try:
            # Read the request line
            request_line = await reader.readline()
            request_str = request_line.decode().strip()
            logger.debug("Received request: %s", request_str)

            # Skip headers until empty line
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n") or not line:
                    break

            # Extract the authorization code from the query string
            if "GET" in request_str and "/auth/callback" in request_str:
                path = request_str.split()[1]
                parsed = urlparse(path)
                query_params = parse_qs(parsed.query)
                logger.debug("Query params: %s", query_params)

                response_body, status_code = _build_callback_response(
                    query_params,
                    auth_code_holder,
                )
            else:
                response_body = "<html><body><h1>Wrong Path</h1><p>Expected callback at /auth/callback</p></body></html>"
                status_code = HTTP_400

            response = _build_http_response(status_code, response_body)
            writer.write(response.encode())
            await writer.drain()
            writer.close()

            # Always signal completion when we get a request
            done_event.set()

        except Exception:
            logger.exception("Error handling callback")
            done_event.set()

    try:
        server = await asyncio.start_server(handle_callback, "localhost", port)
    except OSError:
        logger.warning("Port %s already in use, trying %s", port, port + 1)
        server = await asyncio.start_server(
            handle_callback,
            "localhost",
            port + 1,
        )
        port = port + 1

    logger.info("Started callback server on http://localhost:%s", port)

    async with server:
        await done_event.wait()

    return auth_code_holder.get("code", "")


def _build_callback_response(
    query_params: dict,
    auth_code_holder: dict[str, str],
) -> tuple[str, int]:
    """Build HTTP response body and status code based on OAuth callback params.

    Returns:
        Tuple of (response_body, status_code)

    """
    if "code" in query_params:
        auth_code_holder["code"] = query_params["code"][0]
        logger.info(
            "Received authorization code: %s...",
            auth_code_holder["code"][:20],
        )
        response_body = (
            "<html><head><script>"
            "setTimeout(function() { window.close(); }, 2000);"
            "</script></head>"
            "<body><h1 style='text-align:center'>Authorization Successful!</h1>"
            "<p style='text-align:center'>You can close this window now.</p>"
            "</body></html>"
        )
        return response_body, HTTP_200

    if "error" in query_params:
        error = query_params.get("error", ["unknown"])[0]
        logger.error("OAuth error: %s", error)
        response_body = f"<html><body><h1>Authorization Failed</h1><p>Error: {error}</p></body></html>"
        return response_body, HTTP_400

    # No code or error in query params
    response_body = "<html><body><h1>Authorization Failed</h1><p>No authorization code received.</p></body></html>"
    return response_body, HTTP_400


def _build_http_response(status_code: int, response_body: str) -> str:
    """Build complete HTTP response.

    Args:
        status_code: HTTP status code
        response_body: HTML response body

    Returns:
        Complete HTTP response string

    """
    status_line = "HTTP/1.1 200 OK" if status_code == HTTP_200 else "HTTP/1.1 400 Bad Request"
    return (
        f"{status_line}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        "Connection: close\r\n\r\n" + response_body
    )


def _update_env_file(key: str, value: str) -> None:
    """Update or add a key-value pair in .env file.

    Args:
        key: The environment variable key
        value: The value to set

    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return

    env_content = env_path.read_text()
    pattern = rf'{key}="[^"]*"'

    if re.search(pattern, env_content):
        env_content = re.sub(pattern, f'{key}="{value}"', env_content)
    else:
        env_content += f'\n{key}="{value}"'

    env_path.write_text(env_content)
    logger.info("Updated .env file with %s", key)


async def _handle_cloud_id_setup(access_token: str) -> None:
    """Handle fetching and saving Jira Cloud ID.

    Args:
        access_token: The OAuth access token

    """
    logger.info("\n--- Step 4: Fetching Jira Cloud ID from Atlassian API ---")
    cloud_id = await fetch_cloud_id_from_api(access_token)

    if cloud_id:
        logger.info("Fetched Jira Cloud ID: %s", cloud_id)
        logger.info("Update your .env file with:")
        logger.info('  JIRA_CLOUD_ID="%s"', cloud_id)
        _update_env_file("JIRA_CLOUD_ID", cloud_id)
        await _handle_project_key_setup(access_token, cloud_id)
    else:
        logger.warning(
            "Could not fetch cloud ID from Atlassian API. You may need to manually set JIRA_CLOUD_ID in .env",
        )


async def _handle_project_key_setup(access_token: str, cloud_id: str) -> None:
    """Handle fetching and saving Jira Project Key.

    Args:
        access_token: The OAuth access token
        cloud_id: The Jira Cloud ID

    """
    logger.info("\n--- Step 5: Fetching Jira Project Key ---")
    project_key = await fetch_project_key_from_api(access_token, cloud_id)

    if project_key:
        logger.info("Found project key: %s", project_key)
        _update_env_file("JIRA_PROJECT_KEY", project_key)
    else:
        logger.warning("Could not fetch project key automatically.")
        logger.info("To complete setup:")
        logger.info("  1. Go to your Jira Cloud instance")
        logger.info("  2. Click on 'Projects' in the sidebar")
        logger.info("  3. Find your project and copy its KEY (e.g., 'PROJ')")
        logger.info('  4. Update .env: JIRA_PROJECT_KEY="PROJ"')
        logger.info("  5. Run this script again")


async def authenticate_with_atlassian() -> None:
    """Handle OAuth 2.0 authentication with Atlassian.

    Steps:
    1. Check for existing valid tokens
    2. Start local HTTP server for callback
    3. Open browser to authorization URL
    4. Exchange authorization code for tokens
    5. Store tokens securely in SQLite database
    """
    logger.info("Starting Atlassian OAuth 2.0 authentication flow...")

    try:
        # Check if we already have valid tokens
        stored_tokens = get_tokens("demo_user")
        if stored_tokens and not is_expired(stored_tokens):
            logger.info("Using existing valid tokens")
            return

        # Step 1: Start callback server
        logger.info("\n--- Step 1: Starting OAuth callback server ---")
        callback_task = asyncio.create_task(start_callback_server(HTTP_PORT))

        # Step 2: Generate authorization URL and open browser
        logger.info("--- Step 2: Opening authorization URL in browser ---")
        auth_url = build_authorize_url("demo_state")
        logger.info("Authorization URL: %s", auth_url)
        logger.info("Opening browser for authorization...")

        # Open the browser
        webbrowser.open(auth_url)

        try:
            # Wait for callback (with timeout)
            auth_code = await asyncio.wait_for(
                callback_task,
                timeout=CALLBACK_TIMEOUT,
            )

            if not auth_code:
                logger.error("Authorization failed: no code received")
                return

            # Step 3: Exchange code for tokens
            logger.info("\n--- Step 3: Exchanging code for access tokens ---")
            access_token, _, expires_in = await exchange_code_for_tokens(
                "demo_user",
                auth_code,
            )

            if access_token:
                logger.info("Successfully obtained and stored access tokens")
                logger.info("Access token stored for user: demo_user")
                logger.info("Token expires in: %s seconds", expires_in)
                await _handle_cloud_id_setup(access_token)
            else:
                logger.error("Failed to exchange code for tokens")

        except TimeoutError:
            logger.exception(
                "Authorization timeout: no callback received within 5 minutes",
            )
        except EOFError:
            logger.warning("Non-interactive environment - skipping OAuth setup")
            logger.info("Ensure your .env file contains:")
            logger.info("  - OAUTH_CLIENT_ID")
            logger.info("  - OAUTH_CLIENT_SECRET")
            logger.info("  - OAUTH_REDIRECT_URI")
            logger.info("  - JIRA_CLOUD_ID")

    except ImportError:
        logger.exception("Cannot import ticket_impl modules")
        logger.info("Please ensure ticket_impl package is properly implemented")


async def _demo_create_ticket(ticket_service: TicketImpl) -> str | None:
    """Demo 1: Create a new ticket.

    Returns:
        The created ticket ID, or None if creation failed

    """
    logger.info("\n--- Demo 1: Creating a new ticket ---")
    try:
        new_ticket = await ticket_service.create_ticket(
            title="Demo Ticket: Feature Implementation",
            description="This is a demo ticket created by the script",
            reporter="demo_user",
            priority=TicketPriority.MEDIUM,
            assignee=None,
        )
    except Exception:
        logger.exception("Failed to create ticket")
    else:
        logger.info("Created ticket: %s", new_ticket.id)
        logger.info("  Title: %s", new_ticket.title)
        logger.info("  Priority: %s", new_ticket.priority)
        return new_ticket.id
    return None


async def _demo_retrieve_ticket(ticket_service: TicketImpl, ticket_id: str) -> None:
    """Demo 2: Retrieve a ticket."""
    logger.info("\n--- Demo 2: Retrieving the created ticket ---")
    try:
        retrieved_ticket = await ticket_service.get_ticket(ticket_id)
        logger.info("Retrieved ticket: %s", retrieved_ticket.id)
        logger.info("  Title: %s", retrieved_ticket.title)
        logger.info("  Status: %s", retrieved_ticket.status)
        logger.info("  Priority: %s", retrieved_ticket.priority)
    except Exception:
        logger.exception("Failed to retrieve ticket")


async def _demo_list_tickets(ticket_service: TicketImpl) -> None:
    """Demo 3: List tickets."""
    logger.info("\n--- Demo 3: Listing recent tickets ---")
    try:
        tickets = await ticket_service.list_tickets(limit=5)
        logger.info("Retrieved %s tickets:", len(tickets))
        for idx, ticket in enumerate(tickets, 1):
            logger.info(
                "  %s. %s (ID: %s, Status: %s)",
                idx,
                ticket.title,
                ticket.id,
                ticket.status,
            )
    except Exception:
        logger.exception("Failed to list tickets")


async def _demo_update_ticket(ticket_service: TicketImpl, ticket_id: str) -> None:
    """Demo 4: Update ticket status."""
    logger.info("\n--- Demo 4: Updating ticket status ---")
    try:
        updated_ticket = await ticket_service.update_ticket(
            ticket_id=ticket_id,
            status=TicketStatus.IN_PROGRESS,
        )
        logger.info("Updated ticket: %s", updated_ticket.id)
        logger.info("  New Status: %s", updated_ticket.status)
        logger.info("  Priority: %s", updated_ticket.priority)
    except Exception:
        logger.exception("Failed to update ticket")


async def _demo_add_comment(ticket_service: TicketImpl, ticket_id: str) -> None:
    """Demo 5: Add a comment to a ticket."""
    logger.info("\n--- Demo 5: Adding a comment to the ticket ---")
    try:
        comment = await ticket_service.add_comment(
            ticket_id=ticket_id,
            author="demo_user",
            content="Demo comment added by script. Great progress!",
        )
        if comment:
            logger.info("Comment added to ticket %s", ticket_id)
            logger.info("  Comment: %s", comment.content)
        else:
            logger.warning("Comment was not created")
    except Exception:
        logger.exception("Failed to add comment")


async def _demo_get_comments(ticket_service: TicketImpl, ticket_id: str) -> None:
    """Demo 6: Retrieve ticket comments."""
    logger.info("\n--- Demo 6: Retrieving ticket comments ---")
    try:
        comments = await ticket_service.get_ticket_comments(ticket_id)
        logger.info("Retrieved %s comments:", len(comments))
        for idx, comment in enumerate(comments, 1):
            logger.info("  %s. %s", idx, comment.content)
    except Exception:
        logger.exception("Failed to retrieve comments")


async def _demo_delete_ticket(ticket_service: TicketImpl, ticket_id: str) -> None:
    """Demo 7: Delete a ticket (with confirmation)."""
    logger.info("\n--- Demo 7: Ticket deletion ---")
    try:
        confirmation = input(
            "Delete the demo ticket? (type 'DELETE' to confirm): ",
        ).strip()
        if confirmation == "DELETE":
            success = await ticket_service.delete_ticket(ticket_id)
            if success:
                logger.info("Ticket %s successfully deleted", ticket_id)
            else:
                logger.warning("Failed to delete ticket %s", ticket_id)
        else:
            logger.info("Deletion cancelled")
    except EOFError:
        logger.info("Non-interactive environment - skipping deletion demo")


async def _run_ticket_demo(ticket_service: TicketImpl) -> None:
    """Run all ticket operation demonstrations.

    Args:
        ticket_service: The ticket service implementation

    """
    demo_ticket_id = await _demo_create_ticket(ticket_service)
    if not demo_ticket_id:
        return

    await _demo_retrieve_ticket(ticket_service, demo_ticket_id)
    await _demo_list_tickets(ticket_service)
    await _demo_update_ticket(ticket_service, demo_ticket_id)
    await _demo_add_comment(ticket_service, demo_ticket_id)
    await _demo_get_comments(ticket_service, demo_ticket_id)
    await _demo_delete_ticket(ticket_service, demo_ticket_id)


async def demo_ticket_operations() -> None:
    """Demonstrate all ticket service operations.

    Operations demonstrated:
    1. Create a new ticket
    2. Retrieve a ticket by ID
    3. List tickets
    4. Update ticket status and priority
    5. Add comments to a ticket
    6. Retrieve comments
    7. Delete a ticket (with confirmation)
    """
    # Check if project key is configured
    project_key = os.getenv("JIRA_PROJECT_KEY", "").strip()
    if not project_key or project_key == "your-project-key-here":
        logger.info("\n--- Skipping Ticket Demo ---")
        logger.info("Project key not configured yet.")
        logger.info(
            "Once you've set JIRA_PROJECT_KEY in .env, run this script again",
        )
        return

    logger.info("\n--- Initializing Jira Ticket Service ---")

    try:
        # Verify we have tokens
        tokens = get_tokens("demo_user")
        if not tokens or is_expired(tokens):
            logger.error("No valid tokens found. Please authenticate first.")
            return

        # Initialize the ticket service implementation
        ticket_service = TicketImpl(user_id="demo_user", project_key=project_key)
        logger.info("Ticket service initialized successfully")
        logger.info("  Using project key: %s", project_key)

        await _run_ticket_demo(ticket_service)

    except ImportError:
        logger.exception("Cannot import ticket service modules")
        logger.info("Please ensure the following packages are implemented:")
        logger.info("  - ticket_impl")
        logger.info("  - ticket_api")


async def main() -> None:
    """Run the Jira ticket service demo.

    This is the main entry point that orchestrates the full demo workflow.
    """
    logger.info("Jira Ticket Service Demo Script")

    # Step 1: Authenticate with Atlassian
    await authenticate_with_atlassian()

    # Step 2: Demonstrate ticket operations
    await demo_ticket_operations()


if __name__ == "__main__":
    asyncio.run(main())
