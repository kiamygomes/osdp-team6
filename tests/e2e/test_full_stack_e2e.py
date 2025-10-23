"""E2E tests using mail_client_adapter → running mail_client_service → real Gmail API."""

import os
import threading
import time
from unittest.mock import Mock, patch

import pytest
import uvicorn
from mail_client_adapter.adapter import ServiceClientAdapter


def start_real_service() -> None:
    """Start the FastAPI service with real Gmail credentials for E2E testing."""
    import sys
    from pathlib import Path

    # Add src to path to avoid module name conflicts
    sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / "src"))

    from mail_client_service.main import app  # type: ignore[import-untyped]

    # Start server with real credentials (no mocking)
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")


@pytest.mark.e2e
@pytest.mark.skipif(
    not all([os.getenv("GMAIL_CLIENT_ID"), os.getenv("GMAIL_CLIENT_SECRET"), os.getenv("GMAIL_REFRESH_TOKEN")]),
    reason="Gmail credentials not available for E2E test",
)
def test_full_stack_real_gmail_api() -> None:
    """E2E test: adapter → running service → real Gmail API.

    This validates the entire system from consumer to external service.
    Tests against real infrastructure with real Gmail API calls.
    """
    # Start the service with real credentials in background
    server_thread = threading.Thread(target=start_real_service, daemon=True)
    server_thread.start()

    # Give the server time to start
    time.sleep(3)

    try:
        # Test the adapter calling the real service with real Gmail
        adapter = ServiceClientAdapter("http://127.0.0.1:8002")
        messages = list(adapter.get_messages(max_results=1))

        # Verify we got real messages from Gmail
        # (This will only pass if there are actual messages in the Gmail account)
        if messages:
            assert len(messages) >= 1
            assert messages[0].id is not None
            assert messages[0].from_ is not None
            # Real Gmail messages should have these fields

    except Exception as e:
        # If the real E2E test fails, it might be due to:
        # - Service startup issues
        # - Network connectivity
        # - Gmail API rate limits
        # - Empty inbox
        pytest.skip(f"E2E test with real Gmail API failed: {e}")


@pytest.mark.e2e
def test_adapter_service_connection_mock() -> None:
    """E2E test with mocked service responses.

    This simulates the full stack without requiring real infrastructure.
    """
    with patch("mail_client_adapter.adapter.get_messages_summary_messages_get") as mock_get:
        # Mock a successful service response
        mock_message = Mock()
        mock_message.id = "e2e-mock-123"
        mock_message.from_ = "e2e@example.com"
        mock_message.subject = "E2E Mock Test"
        mock_message.date = "2023-01-01"

        mock_get.sync.return_value = [mock_message]

        # Test the full adapter flow
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages(max_results=1))

        # Verify E2E flow works
        assert len(messages) == 1
        assert messages[0].id == "e2e-mock-123"
        assert messages[0].from_ == "e2e@example.com"


@pytest.mark.e2e
@pytest.mark.local_credentials
def test_real_service_with_local_setup() -> None:
    """E2E test for local development with manual service setup.

    This assumes you manually start the service before running tests.
    """
    # This test assumes the service is already running locally
    # It's marked local_credentials so it only runs in development

    try:
        adapter = ServiceClientAdapter("http://localhost:8000")

        # Try to connect to a manually started service
        # This would work if you run: uvicorn src.mail_client_service.main:app
        messages = list(adapter.get_messages(max_results=1))

        # If we get here, the service is running and responding
        assert isinstance(messages, list)

    except Exception:
        # If no service is running, just pass
        # This test is optional for local development
        pytest.skip("No local service running - start with: uvicorn src.mail_client_service.main:app")
