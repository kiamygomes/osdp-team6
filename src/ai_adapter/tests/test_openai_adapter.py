"""Unit tests for OpenAI adapter."""

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from ticket_api import Ticket, TicketPriority, TicketStatus

from ticket_ai_adapter.openai_adapter import OpenAITicketAdapter


class TestOpenAITicketAdapter:
    """Test OpenAI ticket adapter."""

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_ticket_service: AsyncMock) -> OpenAITicketAdapter:
        """Create OpenAI adapter with mocked client."""
        adapter = OpenAITicketAdapter(
            ticket_service=mock_ticket_service,
            openai_api_key="sk-test-key",
            user_id="test@example.com",
            model="gpt-4o-mini",
        )
        adapter.openai_client = Mock()
        return adapter

    @pytest.mark.asyncio
    async def test_process_command_create_ticket(
        self,
        adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test processing create ticket command."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "tool": "create_ticket",
            "parameters": {
                "title": "Test Ticket",
                "description": "Test Description",
                "priority": "high",
            },
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        adapter.openai_client.chat.completions.create.return_value = mock_response  # type: ignore[attr-defined]

        # Mock ticket service
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Process command
        result = await adapter.process_command("Create a high priority test ticket")

        assert result.success
        assert "Test Ticket" in result.message
        assert result.data == expected_ticket

    @pytest.mark.asyncio
    async def test_process_command_no_tool_call(
        self,
        adapter: OpenAITicketAdapter,
    ) -> None:
        """Test processing command that doesn't result in tool call."""
        # Mock OpenAI response without tool call
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({"message": "I need more information"})
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        adapter.openai_client.chat.completions.create.return_value = mock_response  # type: ignore[attr-defined]

        result = await adapter.process_command("What can you do?")

        assert result.success
        assert "message" in result.message

    @pytest.mark.asyncio
    async def test_process_command_empty_response(
        self,
        adapter: OpenAITicketAdapter,
    ) -> None:
        """Test handling empty response from OpenAI."""
        mock_response = Mock()
        mock_response.choices = []
        adapter.openai_client.chat.completions.create.return_value = mock_response  # type: ignore[attr-defined]

        result = await adapter.process_command("Test")

        assert not result.success
        assert "Failed to get response" in result.message

    @pytest.mark.asyncio
    async def test_process_command_service_error(
        self,
        adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test handling service error."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps({
            "tool": "create_ticket",
            "parameters": {"title": "Test", "description": "Test"},
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        adapter.openai_client.chat.completions.create.return_value = mock_response  # type: ignore[attr-defined]

        # Mock service error
        from ticket_api import ServiceError
        mock_ticket_service.create_ticket.side_effect = ServiceError("Service unavailable")

        result = await adapter.process_command("Create ticket")

        assert not result.success
        assert "Failed to execute" in result.message

    def test_system_prompt_contains_tools(self, adapter: OpenAITicketAdapter) -> None:
        """Test that system prompt includes tool definitions."""
        assert "create_ticket" in adapter._system_prompt
        assert "get_ticket" in adapter._system_prompt
        assert "list_tickets" in adapter._system_prompt
        assert "update_ticket" in adapter._system_prompt
        assert "add_comment" in adapter._system_prompt
