"""Integration test: ServiceClientAdapter → FastAPI service (mocked Gmail client).

This test focuses on the adapter-to-service integration without hitting real Gmail API.
It verifies that the adapter correctly transforms requests/responses through the HTTP layer.
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from mail_client_adapter.adapter import MessageNotFoundError, ServiceClientAdapter
from mail_client_service.main import app, get_mail_client

from mail_client_api import Client, Message


@pytest.fixture
def mock_gmail_client() -> Client:
    """Create a mock Gmail client for testing."""
    mock_client = Mock(spec=Client)

    # Setup default mock message
    mock_message = Mock(spec=Message)
    mock_message.id = "msg_123"
    mock_message.from_ = "sender@example.com"
    mock_message.to = "recipient@example.com"
    mock_message.date = "2024-01-01"
    mock_message.subject = "Test Subject"
    mock_message.body = "Test body content"

    # Configure mock client methods
    mock_client.get_messages.return_value = [mock_message]
    mock_client.get_message.return_value = mock_message
    mock_client.mark_as_read.return_value = True
    mock_client.delete_message.return_value = True

    return mock_client


@pytest.fixture
def adapter_with_service(mock_gmail_client: Client) -> ServiceClientAdapter:
    """Create adapter connected to FastAPI service with mocked client."""
    # Override dependency with mock
    app.dependency_overrides[get_mail_client] = lambda: mock_gmail_client

    # Create TestClient
    test_client = TestClient(app)

    # Create adapter
    adapter = ServiceClientAdapter(base_url="http://testserver")
    adapter._client._client = test_client

    yield adapter, mock_gmail_client
    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_adapter_get_messages_calls_service(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter.get_messages() calls service endpoint correctly."""
    adapter, mock_client = adapter_with_service

    # Call through adapter
    messages = list(adapter.get_messages(max_results=5))

    # Verify adapter got messages
    assert len(messages) == 1
    assert messages[0].id == "msg_123"
    assert hasattr(messages[0], "from_")
    assert messages[0].subject == "Test Subject"

    # Verify service called the client with correct params
    mock_client.get_messages.assert_called_once_with(max_results=5)


@pytest.mark.integration
def test_adapter_get_message_detail_calls_service(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter.get_message() retrieves message details through service."""
    adapter, mock_client = adapter_with_service

    # Call through adapter
    message = adapter.get_message("msg_123")

    # Verify adapter got full message details
    assert message.id == "msg_123"
    assert hasattr(message, "from_")
    assert message.body == "Test body content"

    # Verify service called the client
    mock_client.get_message.assert_called_once_with("msg_123")



@pytest.mark.integration
def test_adapter_mark_as_read_calls_service(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter.mark_as_read() calls service endpoint."""
    adapter, mock_client = adapter_with_service

    # Call through adapter
    result = adapter.mark_as_read("msg_123")
    assert result is not None

    # Verify service called the client
    mock_client.mark_as_read.assert_called_once_with("msg_123")


@pytest.mark.integration
def test_adapter_delete_message_calls_service(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter.delete_message() calls service endpoint."""
    adapter, mock_client = adapter_with_service

    # Call through adapter
    result = adapter.delete_message("msg_123")
    assert result is not None

    # Verify service called the client
    mock_client.delete_message.assert_called_once_with("msg_123")


@pytest.mark.integration
def test_adapter_handles_service_404_error(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter properly handles 404 from service."""
    adapter, mock_client = adapter_with_service

    # Make client raise exception
    mock_client.get_message.side_effect = Exception("Message not found")

    # Verify adapter raises appropriate error
    with pytest.raises(MessageNotFoundError):
        adapter.get_message("nonexistent")


@pytest.mark.integration
def test_adapter_handles_empty_message_list(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter handles empty message list from service."""
    adapter, mock_client = adapter_with_service

    # Return empty list
    mock_client.get_messages.return_value = []
    messages = list(adapter.get_messages(max_results=10))

    # Verify empty list handled correctly
    assert messages == []
    assert isinstance(messages, list)


@pytest.mark.integration
def test_adapter_handles_service_error_responses(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test adapter handles various service error responses."""
    adapter, mock_client = adapter_with_service

    # Simulate service error
    mock_client.get_messages.side_effect = Exception("Service error")
    messages = list(adapter.get_messages())

    # Verify adapter handled the error gracefully (returns empty list)
    assert messages == []


@pytest.mark.integration
def test_adapter_transforms_message_data_correctly(adapter_with_service: tuple[ServiceClientAdapter, Client]) -> None:
    """Test that adapter correctly transforms Message objects through HTTP."""
    adapter, mock_client = adapter_with_service

    # Create message with specific data
    mock_msg = Mock(spec=Message)
    mock_msg.id = "test_id_456"
    mock_msg.from_ = "test@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.date = "2024-10-23"
    mock_msg.subject = "Integration Test"
    mock_msg.body = "This is a test body"

    mock_client.get_message.return_value = mock_msg

    # Get through adapter
    result = adapter.get_message("test_id_456")
    assert result.id == "test_id_456"
    assert result.to == "recipient@example.com"
    assert result.date == "2024-10-23"
    assert result.subject == "Integration Test"
    assert result.body == "This is a test body"
