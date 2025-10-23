"""Integration test: FastAPI service with real GmailClient."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from mail_client_service.main import app, get_mail_client

from gmail_client_impl import GmailClient


@pytest.mark.integration
@pytest.mark.circleci
def test_service_get_messages_with_real_client() -> None:
    """Test FastAPI endpoints call real GmailClient."""
    def get_real_client() -> GmailClient:
        # Handle missing credentials in CircleCI env
        try:
            return GmailClient(interactive=False)
        except RuntimeError:
            try:
                return GmailClient(interactive=True)
            except (RuntimeError, FileNotFoundError):
                # Re-raise the original error to be caught below
                msg = "No valid credentials available"
                raise RuntimeError(msg) from None

    app.dependency_overrides[get_mail_client] = get_real_client

    try:
        client = TestClient(app)
        response = client.get("/messages?max_results=2")

        # If we get 503, credentials weren't available - skip the test
        if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            response_data = response.json()
            if "Authentication error" in response_data.get("detail", "") or \
               "Failed to initialize" in response_data.get("detail", ""):
                pytest.skip("No valid credentials available for integration test")
            # If it's a different 503 error, fail the test
            pytest.fail(f"Service unavailable: {response_data.get('detail')}")

        # Otherwise, expect success
        assert response.status_code == HTTPStatus.OK, f"Expected 200, got {response.status_code}: {response.json()}"
        messages = response.json()
        assert isinstance(messages, list), f"Expected list, got {type(messages)}"

        # Verify actual Message → Pydantic model transformation
        if messages:
            first_message = messages[0]
            assert "id" in first_message, "Message missing 'id' field"
            assert "from" in first_message or "from_" in first_message, "Message missing 'from' field"
            assert "subject" in first_message, "Message missing 'subject' field"

    finally:
        app.dependency_overrides.clear()
