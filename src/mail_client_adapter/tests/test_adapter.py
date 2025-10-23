"""Tests for the ServiceClientAdapter."""

import pytest
from unittest.mock import Mock, patch

from mail_client_adapter.adapter import ServiceClientAdapter, ServiceMessage


class MockMessageSummary:
    """Mock class that behaves like MessageSummary."""
    def __init__(self, id=None, from_=None, date=None, subject=None):
        self.id = id
        self.from_ = from_
        self.date = date
        self.subject = subject


class MockMessageDetail:
    """Mock class that behaves like MessageDetail."""
    def __init__(self, id=None, from_=None, to=None, date=None, subject=None, body=None):
        self.id = id
        self.from_ = from_
        self.to = to
        self.date = date
        self.subject = subject
        self.body = body


class TestServiceMessage:
    """Test the ServiceMessage wrapper class."""

    def test_service_message_with_summary(self):
        """Test ServiceMessage with MessageSummary."""
        summary = MockMessageSummary(
            id="test-id",
            from_="sender@example.com",
            date="2023-01-01",
            subject="Test Subject"
        )
        
        msg = ServiceMessage(summary)
        
        assert msg.id == "test-id"
        assert msg.from_ == "sender@example.com"
        assert msg.date == "2023-01-01"
        assert msg.subject == "Test Subject"
        assert msg.to == ""  # Not available in summary
        assert msg.body == ""  # Not available in summary

    @patch('mail_client_adapter.adapter.MessageDetail', MockMessageDetail)
    def test_service_message_with_detail(self):
        """Test ServiceMessage with MessageDetail."""
        detail = MockMessageDetail(
            id="test-id",
            from_="sender@example.com",
            to="recipient@example.com",
            date="2023-01-01",
            subject="Test Subject",
            body="Test Body"
        )
        
        msg = ServiceMessage(detail)
        
        assert msg.id == "test-id"
        assert msg.from_ == "sender@example.com"
        assert msg.to == "recipient@example.com"
        assert msg.date == "2023-01-01"
        assert msg.subject == "Test Subject"
        assert msg.body == "Test Body"

    def test_service_message_with_none_values(self):
        """Test ServiceMessage handles None values gracefully."""
        summary = MockMessageSummary(
            id=None,
            from_=None,
            date=None,
            subject=None
        )
        
        msg = ServiceMessage(summary)
        
        assert msg.id == ""
        assert msg.from_ == ""
        assert msg.date == ""
        assert msg.subject == ""


class TestServiceClientAdapter:
    """Test the ServiceClientAdapter class."""

    def test_init(self):
        """Test adapter initialization."""
        adapter = ServiceClientAdapter("http://localhost:8000")
        assert adapter._client is not None

    @patch('mail_client_adapter.adapter.get_messages_summary_messages_get')
    def test_get_messages_success(self, mock_get_messages):
        """Test successful message retrieval."""
        # Setup
        mock_summaries = [
            MockMessageSummary(id="1", from_="test1@example.com", subject="Subject 1", date="2023-01-01"),
            MockMessageSummary(id="2", from_="test2@example.com", subject="Subject 2", date="2023-01-02")
        ]
        mock_get_messages.sync.return_value = mock_summaries
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        
        # Execute
        messages = list(adapter.get_messages(max_results=2))
        
        # Assert
        assert len(messages) == 2
        assert messages[0].id == "1"
        assert messages[1].id == "2"
        mock_get_messages.sync.assert_called_once_with(client=adapter._client, max_results=2)

    @patch('mail_client_adapter.adapter.get_messages_summary_messages_get')
    def test_get_messages_empty_response(self, mock_get_messages):
        """Test get_messages with empty response."""
        mock_get_messages.sync.return_value = []
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages())
        
        assert len(messages) == 0

    @patch('mail_client_adapter.adapter.get_messages_summary_messages_get')
    def test_get_messages_none_response(self, mock_get_messages):
        """Test get_messages with None response."""
        mock_get_messages.sync.return_value = None
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        messages = list(adapter.get_messages())
        
        assert len(messages) == 0

    @patch('mail_client_adapter.adapter.get_message_detail_messages_message_id_get')
    @patch('mail_client_adapter.adapter.MessageDetail', MockMessageDetail)
    def test_get_message_success(self, mock_get_message):
        """Test successful single message retrieval."""
        mock_detail = MockMessageDetail(
            id="test-id",
            from_="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            date="2023-01-01"
        )
        mock_get_message.sync.return_value = mock_detail
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        message = adapter.get_message("test-id")
        
        assert message.id == "test-id"
        assert message.body == "Test Body"
        mock_get_message.sync.assert_called_once_with(client=adapter._client, message_id="test-id")

    @patch('mail_client_adapter.adapter.get_message_detail_messages_message_id_get')
    def test_get_message_not_found(self, mock_get_message):
        """Test get_message when message not found."""
        mock_get_message.sync.return_value = None
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        
        with pytest.raises(Exception, match="Message test-id not found"):
            adapter.get_message("test-id")

    @patch('mail_client_adapter.adapter.delete_message_messages_message_id_delete')
    def test_delete_message_success(self, mock_delete):
        """Test successful message deletion."""
        mock_delete.sync.return_value = {"success": True}
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.delete_message("test-id")
        
        assert result is True
        mock_delete.sync.assert_called_once_with(client=adapter._client, message_id="test-id")

    @patch('mail_client_adapter.adapter.delete_message_messages_message_id_delete')
    def test_delete_message_failure(self, mock_delete):
        """Test message deletion failure."""
        mock_delete.sync.side_effect = Exception("API Error")
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.delete_message("test-id")
        
        assert result is False

    @patch('mail_client_adapter.adapter.delete_message_messages_message_id_delete')
    def test_delete_message_none_response(self, mock_delete):
        """Test delete_message with None response."""
        mock_delete.sync.return_value = None
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.delete_message("test-id")
        
        assert result is False

    @patch('mail_client_adapter.adapter.mark_message_as_read_messages_message_id_mark_as_read_post')
    def test_mark_as_read_success(self, mock_mark_read):
        """Test successful mark as read."""
        mock_mark_read.sync.return_value = {"success": True}
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.mark_as_read("test-id")
        
        assert result is True
        mock_mark_read.sync.assert_called_once_with(client=adapter._client, message_id="test-id")

    @patch('mail_client_adapter.adapter.mark_message_as_read_messages_message_id_mark_as_read_post')
    def test_mark_as_read_failure(self, mock_mark_read):
        """Test mark as read failure."""
        mock_mark_read.sync.side_effect = Exception("API Error")
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.mark_as_read("test-id")
        
        assert result is False

    @patch('mail_client_adapter.adapter.mark_message_as_read_messages_message_id_mark_as_read_post')
    def test_mark_as_read_none_response(self, mock_mark_read):
        """Test mark_as_read with None response."""
        mock_mark_read.sync.return_value = None
        
        adapter = ServiceClientAdapter("http://localhost:8000")
        result = adapter.mark_as_read("test-id")
        
        assert result is False