"""Tests for the mail client service Pydantic models."""

import pytest
from pydantic import ValidationError

from mail_client_service.models import (
    ErrorResponse,
    MessageDetail,
    MessageListResponse,
    MessageSummary,
    SuccessResponse,
)


def test_message_summary_creation():
    """Test MessageSummary model creation."""
    summary = MessageSummary(
        id="msg_123",
        from_="sender@example.com",
        to="recipient@example.com",
        date="2023-01-01",
        subject="Test Subject"
    )
    # Assertions
    assert summary.id == "msg_123"
    assert summary.from_ == "sender@example.com"


def test_message_summary_from_alias():
    """Test MessageSummary 'from' field alias works."""
    summary = MessageSummary(
        id="msg_123",
        **{"from": "sender@example.com"},  # Using alias
        to="recipient@example.com",
        date="2023-01-01",
        subject="Test Subject"
    )
    # Assertions
    assert summary.from_ == "sender@example.com"


def test_message_detail_creation():
    """Test MessageDetail model creation."""
    detail = MessageDetail(
        id="msg_123",
        from_="sender@example.com",
        to="recipient@example.com",
        date="2023-01-01",
        subject="Test Subject",
        body="Message body"
    )
    # Assertions
    assert detail.body == "Message body"


def test_message_list_response():
    """Test MessageListResponse model."""
    message = MessageSummary(
        id="msg_1",
        from_="sender@example.com",
        to="recipient@example.com",
        date="2023-01-01",
        subject="Subject"
    )
    # Act
    response = MessageListResponse(messages=[message], count=1)
    # Assertions
    assert len(response.messages) == 1
    assert response.count == 1


def test_success_response():
    """Test SuccessResponse model."""
    response = SuccessResponse(success=True, message="Success!")
    # Assertions
    assert response.success is True
    assert response.message == "Success!"


def test_error_response():
    """Test ErrorResponse model."""
    response = ErrorResponse(error="Error occurred", detail="More info")
    # Assertions
    assert response.error == "Error occurred"
    assert response.detail == "More info"


def test_error_response_without_detail():
    """Test ErrorResponse without optional detail."""
    response = ErrorResponse(error="Error occurred")
    # Assertions
    assert response.error == "Error occurred"
    assert response.detail is None