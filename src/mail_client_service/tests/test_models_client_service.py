"""Tests for the mail client service Pydantic models."""

from mail_client_service.models import (
    ErrorResponse,
    MessageDetail,
    MessageListResponse,
    MessageSummary,
    SuccessResponse,
)


def test_message_summary_creation() -> None:
    """Creates a MessageSummary and verifies the id and 'from' alias map to attributes."""
    # Arrange
    payload = {
        "id": "msg_123",
        **{"from": "sender@example.com"},  # Use alias
        "to": "recipient@example.com",
        "date": "2023-01-01",
        "subject": "Test Subject",
    }

    # Act
    summary = MessageSummary(**payload)

    # Assert
    assert summary.id == "msg_123"
    assert summary.from_ == "sender@example.com"


def test_message_summary_from_alias() -> None:
    """Test MessageSummary 'from' field alias works."""
    # Arrange
    payload = {
        "id": "msg_123",
        **{"from": "sender@example.com"},  # Using alias
        "to": "recipient@example.com",
        "date": "2023-01-01",
        "subject": "Test Subject",
    }

    # Act
    summary = MessageSummary(**payload)

    # Assert
    assert summary.from_ == "sender@example.com"


def test_message_detail_creation() -> None:
    """Test MessageDetail model creation."""
    detail = MessageDetail(
        id="msg_123",
        **{"from": "sender@example.com"},  # Use alias
        to="recipient@example.com",
        date="2023-01-01",
        subject="Test Subject",
        body="Message body",
    )
    # Assertions
    # Arrange
    payload = {
        "id": "msg_123",
        **{"from": "sender@example.com"},  # Use alias
        "to": "recipient@example.com",
        "date": "2023-01-01",
        "subject": "Test Subject",
        "body": "Message body",
    }

    # Act
    detail = MessageDetail(**payload)

    # Assert
    assert detail.body == "Message body"


def test_message_list_response() -> None:
    """Test MessageListResponse model."""
    # Arrange
    message = MessageSummary(
        id="msg_1",
        **{"from": "sender@example.com"},  # Use alias
        **{"from": "sender@example.com"},  # Use alias
        to="recipient@example.com",
        date="2023-01-01",
        subject="Subject",
    )

    # Act
    response = MessageListResponse(messages=[message], count=1)

    # Assert
    assert len(response.messages) == 1
    assert response.count == 1


def test_success_response() -> None:
    """Test SuccessResponse model."""
    # Arrange
    payload = {"success": True, "message": "Success!"}

    # Act
    response = SuccessResponse(**payload)

    # Assert
    assert response.success is True
    assert response.message == "Success!"


def test_error_response() -> None:
    """Test ErrorResponse model."""
    # Arrange
    payload = {"error": "Error occurred", "detail": "More info"}

    # Act
    response = ErrorResponse(**payload)

    # Assert
    assert response.error == "Error occurred"
    assert response.detail == "More info"


def test_error_response_without_detail() -> None:
    """Test ErrorResponse without optional detail."""
    # Arrange
    payload = {"error": "Error occurred", "detail": None}

    # Act
    response = ErrorResponse(**payload)

    # Assert
    assert response.error == "Error occurred"
    assert response.detail is None
