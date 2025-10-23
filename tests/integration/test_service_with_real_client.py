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
        return GmailClient(interactive=True)

    app.dependency_overrides[get_mail_client] = get_real_client

    try:
        client = TestClient(app)
        response = client.get("/messages?max_results=2")

        # If we get 503, it means credentials weren't available
        if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            response_data = response.json()
            if "Authentication error" in response_data.get("detail", ""):
                pytest.skip("No valid credentials available for integration test")

        # Otherwise, expect success
        assert response.status_code == HTTPStatus.OK
        messages = response.json()
        assert isinstance(messages, list)

        # Verify actual Message → Pydantic model transformation
        if messages:
            assert "id" in messages[0]
            assert "from" in messages[0] or "from_" in messages[0]
            assert "subject" in messages[0]

    finally:
        app.dependency_overrides.clear()
