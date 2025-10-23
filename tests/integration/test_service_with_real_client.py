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
    credentials_available = False

    def get_real_client() -> GmailClient:
        nonlocal credentials_available
        # Handle missing credentials in CircleCI env
        try:
            client = GmailClient(interactive=False)
            credentials_available = True
            return client
        except RuntimeError:
            try:
                client = GmailClient(interactive=True)
                credentials_available = True
                return client
            except (RuntimeError, FileNotFoundError):
                credentials_available = False
                pytest.skip("No valid credentials available for integration test")

    app.dependency_overrides[get_mail_client] = get_real_client

    try:
        client = TestClient(app)
        response = client.get("/messages")

        # This code only runs if credentials were available
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
