"""Tests for main_app.py orchestrator."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from orchestrator.main_app import TicketBotOrchestrator, demo_cli, main

load_dotenv()

class MockChatClient:
    """Mock chat client for testing."""

    def __init__(self) -> None:
        """Initialize mock chat client."""
        self.messages: list[MagicMock] = []
        self.sent_messages: list[tuple[str, str]] = []

    def send_message(self, channel_id: str, content: str) -> bool:
        """Mock send message."""
        self.sent_messages.append((channel_id, content))
        return True

    def get_messages(self, channel_id: str, limit: int = 10) -> list[MagicMock]:
        """Mock get messages."""
        return self.messages[:limit]


class TestTicketBotOrchestrator:
    """Test the main orchestrator class."""

    project_key = os.getenv("PROJECT_KEY", "TEST")

    def test_init_claude_provider(self) -> None:
        """Test initialization with Claude provider."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        assert orchestrator.user_id == "demo_user"
        assert orchestrator.project_key == self.project_key
        assert orchestrator.chat_client is None
        assert orchestrator.ticket_service is not None
        assert orchestrator.ai_adapter is not None

    def test_init_openai_provider(self) -> None:
        """Test initialization with OpenAI provider."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="openai",
        )

        assert orchestrator.user_id == "demo_user"
        assert orchestrator.project_key == self.project_key
        assert orchestrator.ai_adapter is not None

    def test_init_invalid_provider(self) -> None:
        """Test initialization with invalid provider."""
        with pytest.raises(ValueError, match="Unknown AI provider: invalid"):
            TicketBotOrchestrator(
                user_id="demo_user",
                project_key=self.project_key,
                ai_provider="invalid",
            )

    def test_init_with_chat_client(self) -> None:
        """Test initialization with chat client."""
        chat_client = MockChatClient()
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
            chat_client=chat_client,
        )

        assert orchestrator.chat_client is chat_client

    @pytest.mark.asyncio
    async def test_process_chat_message_success(self) -> None:
        """Test successful message processing."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        # Mock the AI adapter to return success
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.message = "Ticket created successfully"
        mock_result.data = {"ticket_id": "TEST-123"}
        mock_result.error = None

        with patch.object(orchestrator.ai_adapter, "process_command", AsyncMock(return_value=mock_result)):
            result = await orchestrator.process_chat_message(
                "Create a ticket for testing",
                channel_id="test-channel",
            )

            assert result["success"] is True
            assert result["message"] == "Ticket created successfully"
            assert result["data"] == {"ticket_id": "TEST-123"}
            assert result["error"] is None
            assert result["channel_id"] == "test-channel"

    @pytest.mark.asyncio
    async def test_process_chat_message_failure(self) -> None:
        """Test failed message processing."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        # Mock the AI adapter to return failure
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.message = "Failed to create ticket"
        mock_result.data = None
        mock_result.error = "Invalid input"

        with patch.object(orchestrator.ai_adapter, "process_command", AsyncMock(return_value=mock_result)):
            result = await orchestrator.process_chat_message(
                "Invalid command",
                channel_id="test-channel",
            )

            assert result["success"] is False
            assert result["message"] == "Failed to create ticket"
            assert result["data"] is None
            assert result["error"] == "Invalid input"

    @pytest.mark.asyncio
    async def test_process_chat_message_exception(self) -> None:
        """Test exception handling in message processing."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        # Mock the AI adapter to raise exception
        with patch.object(orchestrator.ai_adapter, "process_command", AsyncMock(side_effect=Exception("Test error"))):
            result = await orchestrator.process_chat_message("Test message")

            assert result["success"] is False
            assert result["message"] == "An unexpected error occurred"
            assert result["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_send_to_chat_with_client(self) -> None:
        """Test sending message with chat client."""
        chat_client = MockChatClient()
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
            chat_client=chat_client,
        )

        result = await orchestrator.send_to_chat("test-channel", "Test message")

        assert result is True
        assert len(chat_client.sent_messages) == 1
        assert chat_client.sent_messages[0] == ("test-channel", "Test message")

    @pytest.mark.asyncio
    async def test_send_to_chat_without_client(self) -> None:
        """Test sending message without chat client (simulation mode)."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        result = await orchestrator.send_to_chat("test-channel", "Test message")

        assert result is True

    @pytest.mark.asyncio
    async def test_send_to_chat_client_error(self) -> None:
        """Test error handling when chat client fails."""
        chat_client = MockChatClient()

        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
            chat_client=chat_client,
        )

        with patch.object(chat_client, "send_message", MagicMock(side_effect=Exception("Chat error"))):
            result = await orchestrator.send_to_chat("test-channel", "Test message")

            assert result is False

    @pytest.mark.asyncio
    async def test_process_incoming_chat_no_client(self) -> None:
        """Test processing incoming chat without client."""
        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
        )

        result = await orchestrator.process_incoming_chat("test-channel")

        assert result == 0

    @pytest.mark.asyncio
    async def test_process_incoming_chat_with_messages(self) -> None:
        """Test processing incoming chat messages."""
        chat_client = MockChatClient()

        # Create mock messages
        msg1 = MagicMock()
        msg1.content = "!ticket create a test ticket"
        msg1.sender_id = "user1"

        msg2 = MagicMock()
        msg2.content = "regular message"
        msg2.sender_id = "user2"

        msg3 = MagicMock()
        msg3.content = "!ticket list tickets"
        msg3.sender_id = "user3"

        chat_client.messages = [msg1, msg2, msg3]

        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
            chat_client=chat_client,
        )

        # Mock the process_chat_message method
        with patch.object(orchestrator, "process_chat_message", AsyncMock(return_value={"message": "Success"})):
            result = await orchestrator.process_incoming_chat("test-channel")

            expected_processed_count = 2  # Only 2 messages with !ticket prefix
            assert result == expected_processed_count
            assert len(chat_client.sent_messages) == expected_processed_count

    @pytest.mark.asyncio
    async def test_process_incoming_chat_exception(self) -> None:
        """Test exception handling in process_incoming_chat."""
        chat_client = MockChatClient()

        orchestrator = TicketBotOrchestrator(
            user_id="demo_user",
            project_key=self.project_key,
            ai_provider="claude",
            chat_client=chat_client,
        )

        with patch.object(chat_client, "get_messages", MagicMock(side_effect=Exception("Chat error"))):
            result = await orchestrator.process_incoming_chat("test-channel")

            assert result == 0


@pytest.mark.asyncio
async def test_demo_cli() -> None:
    """Test the demo CLI function."""
    with patch("orchestrator.main_app.TicketBotOrchestrator") as mock_orchestrator_class:
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_chat_message = AsyncMock()
        mock_orchestrator_class.return_value = mock_orchestrator

        await demo_cli()

        # Should create 2 orchestrators (Claude and OpenAI)
        expected_orchestrator_count = 2
        assert mock_orchestrator_class.call_count == expected_orchestrator_count

        # Should process 3 messages total
        expected_message_count = 3
        assert mock_orchestrator.process_chat_message.call_count == expected_message_count


def test_main() -> None:
    """Test the main function."""
    with patch("orchestrator.main_app.asyncio.run") as mock_run:
        main()
        mock_run.assert_called_once()
