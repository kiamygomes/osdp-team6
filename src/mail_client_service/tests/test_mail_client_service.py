"""Tests for the mail client service FastAPI application."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from mail_client_api import Client, Message
from mail_client_service.main import MessageDetail, MessageSummary, app, get_mail_client


# Test Fixtures
# These fixtures provide reusable mock objects and test client setup
# for testing the endpoints without external dependencies
@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    return Mock(spec=Client)


@pytest.fixture
def mock_message():
    """Create a mock message for testing."""
    msg = Mock(spec=Message)
    msg.id = "msg_123"
    msg.from_ = "sender@example.com"
    msg.to = "recipient@example.com"
    msg.date = "2024-01-01"
    msg.subject = "Test Subject"
    msg.body = "Test body content"
    return msg


@pytest.fixture
def test_client_with_mock(mock_client):
    """Create test client with mocked dependency."""
    app.dependency_overrides[get_mail_client] = lambda: mock_client
    client = TestClient(app)
    yield client, mock_client
    # Cleanup
    app.dependency_overrides.clear()


# Test the dependency function directly (without HTTP)
def test_get_mail_client_success():
    """Test successful mail client initialization."""
    with patch("mail_client_service.main.get_client") as mock_get_client:
        mock_client = Mock(spec=Client)
        mock_get_client.return_value = mock_client

        result = get_mail_client()
        # Assertions
        mock_get_client.assert_called_once_with(interactive=False)
        assert result is mock_client


def test_get_mail_client_runtime_error():
    """Test client initialization failure."""
    with patch("mail_client_service.main.get_client") as mock_get_client:
        mock_get_client.side_effect = RuntimeError("Auth failed")

        with pytest.raises(HTTPException) as exc_info:
            get_mail_client()
        # Assertions
        assert exc_info.value.status_code == 503
        assert "Authentication error" in str(exc_info.value.detail)


# HTTP endpoint tests using the fixture
def test_get_messages_summary_success(test_client_with_mock, mock_message):
    """Test successful message summary retrieval."""
    client, mock_client = test_client_with_mock
    mock_client.get_messages.return_value = [mock_message]

    response = client.get("/messages")
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "msg_123"
    mock_client.get_messages.assert_called_once_with(max_results=10)


def test_get_messages_summary_with_max_results(test_client_with_mock):
    """Test message summary with custom max_results."""
    client, mock_client = test_client_with_mock
    mock_client.get_messages.return_value = []

    response = client.get("/messages?max_results=5")
    # Assertions
    assert response.status_code == 200
    mock_client.get_messages.assert_called_once_with(max_results=5)


def test_get_messages_summary_client_exception(test_client_with_mock):
    """Test error handling when client throws exception."""
    client, mock_client = test_client_with_mock
    mock_client.get_messages.side_effect = Exception("Client error")

    response = client.get("/messages")
    # Assertions
    assert response.status_code == 500
    assert "Failed to fetch messages" in response.json()["detail"]


def test_get_message_detail_success(test_client_with_mock, mock_message):
    """Test successful message detail retrieval."""
    client, mock_client = test_client_with_mock
    mock_client.get_message.return_value = mock_message

    response = client.get("/messages/msg_123")
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "msg_123"
    assert data["from_"] == "sender@example.com"
    mock_client.get_message.assert_called_once_with("msg_123")


def test_get_message_detail_not_found(test_client_with_mock):
    """Test message not found error."""
    client, mock_client = test_client_with_mock
    mock_client.get_message.side_effect = Exception("Not found")

    response = client.get("/messages/nonexistent")
    # Assertions
    assert response.status_code == 404
    assert "not found or inaccessible" in response.json()["detail"]


def test_mark_message_as_read_success(test_client_with_mock):
    """Test successful mark as read."""
    client, mock_client = test_client_with_mock
    mock_client.mark_as_read.return_value = True

    response = client.post("/messages/msg_123/mark-as-read")
    # Assertions
    assert response.status_code == 200
    assert "marked as read" in response.json()["message"]
    mock_client.mark_as_read.assert_called_once_with("msg_123")


def test_mark_message_as_read_failure(test_client_with_mock):
    """Test failed mark as read."""
    client, mock_client = test_client_with_mock
    mock_client.mark_as_read.return_value = False

    response = client.post("/messages/msg_123/mark-as-read")
    # Assertions
    assert response.status_code == 500
    assert "Failed to mark message" in response.json()["detail"]


def test_delete_message_success(test_client_with_mock):
    """Test successful message deletion."""
    client, mock_client = test_client_with_mock
    mock_client.delete_message.return_value = True

    response = client.delete("/messages/msg_123")
    # Assertions
    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
    mock_client.delete_message.assert_called_once_with("msg_123")


def test_delete_message_failure(test_client_with_mock):
    """Test failed message deletion."""
    client, mock_client = test_client_with_mock
    mock_client.delete_message.return_value = False

    response = client.delete("/messages/msg_123")
    # Assertions
    assert response.status_code == 500
    assert "Failed to delete message" in response.json()["detail"]


# Model tests (no HTTP needed)
def test_message_summary_model():
    """Test MessageSummary model."""
    summary = MessageSummary(id="msg_123", from_="test@example.com")
    assert summary.id == "msg_123"
    assert summary.from_ == "test@example.com"


def test_message_detail_model():
    """Test MessageDetail model."""
    detail = MessageDetail(
        id="msg_123",
        from_="sender@example.com",
        to="recipient@example.com",
        date="2024-01-01",
        subject="Test",
        body="Body",
    )
    # Assertions
    assert detail.id == "msg_123"
    assert detail.body == "Body"
