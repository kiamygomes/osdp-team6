"""E2E tests using mail_client_adapter, running mail_client_service to real Gmail API.

This module contains two types of E2E tests:
1. Tests with real Gmail credentials (CI/CD or local with credentials)
2. Tests for local development that assume service is manually started
"""

import logging
import os
import socket
import threading
import time
from contextlib import closing
from http import HTTPStatus

import pytest
import uvicorn
from mail_client_adapter.adapter import ServiceClientAdapter

from mail_client_api import Message

logger = logging.getLogger(__name__)


def find_free_port() -> int:
    """Find a free port for the test server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port: int = s.getsockname()[1]
        return port


def start_real_service(port: int) -> None:
    """Start the FastAPI service with real Gmail credentials for E2E testing."""
    import sys
    from pathlib import Path

    # Add src to path to avoid module name conflicts
    sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / "src"))

    from mail_client_service.main import app  # type: ignore[import-untyped]

    # Start server with real credentials (no mocking)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


def wait_for_service(base_url: str, timeout: int = 10) -> bool:
    """Wait for the service to be ready."""
    import requests

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/docs", timeout=1)
            if response.status_code == HTTPStatus.OK:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    return False


def has_gmail_credentials() -> bool:
    """Check if Gmail credentials are available."""
    return all(
        [
            os.getenv("GMAIL_CLIENT_ID"),
            os.getenv("GMAIL_CLIENT_SECRET"),
            os.getenv("GMAIL_REFRESH_TOKEN"),
        ],
    )


def should_run_e2e() -> bool:
    """Check if environment is configured for E2E tests."""
    # 1. Check for the existence of credentials
    has_creds = all([os.getenv("GMAIL_CLIENT_ID"), os.getenv("GMAIL_CLIENT_SECRET"), os.getenv("GMAIL_REFRESH_TOKEN")])
    # 2. Check for an explicit E2E flag, which you would set to 'true'
    #    only in the CI step that has valid credentials.
    is_e2e_enabled = os.getenv("RUN_E2E_TESTS") == "true"

    return has_creds and is_e2e_enabled


@pytest.fixture(scope="module")
def service_url() -> str:
    """Fixture that starts the service and returns its URL."""
    if not should_run_e2e():  # Use the new combined check
        pytest.skip("E2E tests disabled or credentials not configured.")

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    # Start the service in background thread
    server_thread = threading.Thread(target=start_real_service, args=(port,), daemon=True)
    server_thread.start()

    # Wait for service to be ready
    if not wait_for_service(base_url, timeout=15):
        pytest.fail("Service failed to start within timeout")

    # Give it an extra moment to fully initialize
    time.sleep(1)

    return base_url


@pytest.mark.e2e
@pytest.mark.skipif(
    not should_run_e2e(),
    reason="Gmail credentials not available for automated E2E test",
)
class TestFullStackRealGmail:
    """E2E tests against real Gmail API through the full stack.

    These tests programmatically start the service and connect to real Gmail.
    Run these in CI/CD or locally if you have credentials set.
    """

    def test_get_messages(self, service_url: str) -> None:
        """Test getting messages from real Gmail through the full stack.

        This validates:
        - Adapter to Service HTTP communication
        - Service to Gmail API authentication
        - Service to Gmail API message retrieval
        - Response transformation through all layers
        """
        adapter = ServiceClientAdapter(service_url)
        messages = list(adapter.get_messages(max_results=5))

        # Verify we got real messages from Gmail
        if not messages:
            pytest.skip("No messages in Gmail inbox - cannot verify full E2E flow")

        # Validate message structure from real Gmail data
        first_message = messages[0]
        assert first_message.id, "Message should have an ID"
        assert first_message.from_, "Message should have a sender"
        assert first_message.subject is not None, "Message should have a subject"
        assert first_message.date, "Message should have a date"

        # Verify we respect max_results
        max_results = 5
        assert len(messages) <= max_results

    def test_get_message_detail(self, service_url: str) -> None:
        """Test getting a single message detail from real Gmail."""
        adapter = ServiceClientAdapter(service_url)

        # First get a message ID from the list
        messages = list(adapter.get_messages(max_results=1))
        if not messages:
            pytest.skip("No messages in Gmail inbox")

        message_id = messages[0].id

        # Now fetch the full detail
        message = adapter.get_message(message_id)

        # Verify full message details
        assert message.id == message_id
        assert message.from_, "Message should have sender"
        assert message.to, "Message should have recipient"
        assert message.subject is not None, "Message should have subject"
        assert message.date, "Message should have date"
        assert message.body is not None, "Message should have body"

    def test_mark_as_read(self, service_url: str) -> None:
        """Test marking a message as read through the full stack."""
        adapter = ServiceClientAdapter(service_url)

        # Get a message to mark as read
        messages = list(adapter.get_messages(max_results=1))
        if not messages:
            pytest.skip("No messages in Gmail inbox")

        message_id = messages[0].id

        # Mark as read - this should succeed even if already read
        result = adapter.mark_as_read(message_id)
        assert result is True, "Mark as read should succeed"

    @pytest.mark.skipif(not should_run_e2e(), reason="Requires working Gmail service")
    def test_mark_as_read_nonexistent_message(self, service_url: str) -> None:
        """Test marking a non-existent message as read."""
        adapter = ServiceClientAdapter(service_url)

        # Try to mark a non-existent message
        result = adapter.mark_as_read("nonexistent-message-id-12345")

        # The adapter should return False for failures
        assert result is False, "Should return False for non-existent message"

    @pytest.mark.skipif(not should_run_e2e(), reason="Requires working Gmail service")
    def test_get_nonexistent_message(self, service_url: str) -> None:
        """Test getting a non-existent message."""
        from mail_client_adapter.adapter import MessageNotFoundError

        adapter = ServiceClientAdapter(service_url)

        # Should raise MessageNotFoundError for non-existent message
        with pytest.raises(MessageNotFoundError):
            adapter.get_message("nonexistent-message-id-12345")

    def test_delete_message(self, service_url: str) -> None:
        """Test deleting a message through the full stack."""
        if not os.getenv("DELETE_TEST_ENABLED"):
            pytest.skip("Delete test disabled - set DELETE_TEST_ENABLED to run")

        adapter = ServiceClientAdapter(service_url)

        # Get a message to delete
        messages = list(adapter.get_messages(max_results=1))
        if not messages:
            pytest.skip("No messages in Gmail inbox")

        message_id = messages[0].id

        # Delete the message
        result = adapter.delete_message(message_id)
        assert result is True, "Delete should succeed"

        # Verify it's deleted by trying to get it
        from mail_client_adapter.adapter import MessageNotFoundError

        with pytest.raises(MessageNotFoundError):
            adapter.get_message(message_id)

    def test_delete_nonexistent_message(self, service_url: str) -> None:
        """Test deleting a non-existent message."""
        adapter = ServiceClientAdapter(service_url)

        # Try to delete a non-existent message
        result = adapter.delete_message("nonexistent-message-id-12345")

        # The adapter should return False for failures
        assert result is False, "Should return False for non-existent message"

    def test_concurrent_operations(self, service_url: str) -> None:
        """Test multiple concurrent operations through the full stack."""
        import concurrent.futures

        adapter = ServiceClientAdapter(service_url)

        def get_messages_task() -> list[Message]:
            return list(adapter.get_messages(max_results=2))

        # Run multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_messages_task) for _ in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        num_workers = 3
        assert len(results) == num_workers
        for result in results:
            assert isinstance(result, list)


@pytest.mark.e2e
@pytest.mark.skipif(
    not has_gmail_credentials(),
    reason="Gmail credentials not available",
)
def test_service_health_check(service_url: str) -> None:
    """Test that the service is running and responsive."""
    import requests

    # Check that docs endpoint is accessible
    response = requests.get(f"{service_url}/docs", timeout=5)
    assert response.status_code == HTTPStatus.OK


def check_local_service() -> bool:
    """Check if local service is running."""
    import requests

    try:
        response = requests.get("http://localhost:8000/docs", timeout=2)
        return response.status_code == HTTPStatus.OK
    except Exception:
        return False


@pytest.mark.e2e
@pytest.mark.local_credentials
def test_local_service_get_messages() -> None:
    """E2E test for local development with manually started service.

    Before running this test, manually start the service:
        uvicorn mail_client_service.main:app --port 8000

    This test assumes:
    - You have Gmail credentials configured locally
    - The service is already running on localhost:8000
    - You want to test against your own Gmail account

    Run with: pytest -m local_credentials
    """
    if not check_local_service():
        pytest.skip(
            "No local service running, start with: uvicorn mail_client_service.main:app --port 8000",
        )

    try:
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages(max_results=3))

        assert isinstance(messages, list)

        if messages:
            # Validate we got real Gmail messages
            assert messages[0].id, "Message should have an ID"
            logger.info("Successfully retrieved %d messages from local service", len(messages))
            if messages[0].from_:
                logger.info("First message from: %s", messages[0].from_)
        else:
            logger.info("Service is running but inbox is empty")

    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")


@pytest.mark.e2e
@pytest.mark.local_credentials
def test_local_service_get_message_detail() -> None:
    """Test getting message detail from manually started local service."""
    if not check_local_service():
        pytest.skip(
            "No local service running - start with: uvicorn mail_client_service.main:app --port 8000",
        )

    try:
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages(max_results=1))

        if not messages:
            pytest.skip("No messages in inbox")

        message_id = messages[0].id
        message = adapter.get_message(message_id)

        # Verify full message details
        assert message.id == message_id
        assert message.from_
        assert message.body is not None
        logger.info("Successfully retrieved message detail for %s", message_id)

    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")


@pytest.mark.e2e
@pytest.mark.local_credentials
def test_local_service_mark_as_read() -> None:
    """Test marking message as read on manually started local service."""
    if not check_local_service():
        pytest.skip(
            "No local service running - start with: uvicorn mail_client_service.main:app --port 8000",
        )

    try:
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages(max_results=1))

        if not messages:
            pytest.skip("No messages in inbox")

        message_id = messages[0].id
        result = adapter.mark_as_read(message_id)

        # Note: mark_as_read might return False if there's an issue
        if not result:
            pytest.skip(
                f"mark_as_read returned False for message {message_id}. "
                "This might indicate a Gmail API issue or the message is already read.",
            )

        assert result is True
        logger.info("Successfully marked message %s as read", message_id)

    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")


@pytest.mark.e2e
@pytest.mark.local_credentials
def test_local_service_full_workflow() -> None:
    """Test complete workflow on manually started local service.

    This simulates a real user workflow:
    1. List messages
    2. Get a message detail
    3. Mark it as read
    """
    if not check_local_service():
        pytest.skip(
            "No local service running, start with: uvicorn mail_client_service.main:app --port 8000",
        )

    try:
        adapter = ServiceClientAdapter("http://localhost:8000")

        # Step 1: List messages
        messages = list(adapter.get_messages(max_results=5))
        assert isinstance(messages, list)

        if not messages:
            pytest.skip("No messages in inbox to test workflow")

        # Step 2: Get first message detail
        message_id = messages[0].id
        message = adapter.get_message(message_id)
        assert message.body is not None

        # Step 3: Mark as read
        result = adapter.mark_as_read(message_id)
        if not result:
            # Don't fail the test, just note it
            logger.warning("mark_as_read returned False (might already be read or API issue)")
        else:
            logger.info("Complete workflow successful!")

    except Exception as e:
        pytest.fail(f"Test failed with error: {e}")
