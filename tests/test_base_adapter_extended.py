"""Extended tests for base adapter to improve coverage."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from ticket_ai_adapter.base_adapter import BaseTicketAIAdapter
from ticket_ai_adapter.models import ToolCall, ToolCallType

from ticket_api import Ticket, TicketPriority, TicketStatus


class TestBaseTicketAIAdapterExtended:
    """Extended tests for BaseTicketAIAdapter to improve coverage."""

    def test_init_with_project_key(self) -> None:
        """Test initialization with project key."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user", project_key="TEST")

        assert adapter.ticket_service is mock_service
        assert adapter.user_id == "test-user"
        assert adapter.project_key == "TEST"

    def test_init_without_project_key(self) -> None:
        """Test initialization without project key."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        assert adapter.project_key is None

    def test_build_system_prompt(self) -> None:
        """Test system prompt building."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        prompt = adapter._build_system_prompt()

        assert "ticket management assistant" in prompt.lower()
        assert "create_ticket" in prompt
        assert "list_tickets" in prompt
        assert "get_ticket" in prompt
        assert "JSON" in prompt

    def test_validate_required_params_success(self) -> None:
        """Test successful parameter validation."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET, parameters={"title": "Test ticket", "description": "Test description"}
        )

        # Should not raise exception
        adapter._validate_required_params(tool_call, ["title"])

    def test_validate_required_params_missing(self) -> None:
        """Test parameter validation with missing params."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.CREATE_TICKET, parameters={"description": "Test description"})

        with pytest.raises(ValueError, match="Missing required parameters"):
            adapter._validate_required_params(tool_call, ["title"])

    def test_validate_required_params_empty_value(self) -> None:
        """Test parameter validation with empty values."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.CREATE_TICKET, parameters={"title": "", "description": "Test description"})

        with pytest.raises(ValueError, match="Missing required parameters"):
            adapter._validate_required_params(tool_call, ["title"])

    def test_parse_tool_call_from_dict_valid(self) -> None:
        """Test parsing valid tool call from dict."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {"tool": "create_ticket", "parameters": {"title": "Test ticket"}}

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is not None
        assert result.type == ToolCallType.CREATE_TICKET
        assert result.parameters["title"] == "Test ticket"

    def test_parse_tool_call_from_dict_no_tool(self) -> None:
        """Test parsing dict without tool key."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {"parameters": {"title": "Test ticket"}}

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is None

    def test_parse_tool_call_from_dict_invalid_tool_type(self) -> None:
        """Test parsing dict with invalid tool type."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {
            "tool": 123,  # Invalid type
            "parameters": {"title": "Test ticket"},
        }

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is None

    def test_parse_tool_call_from_dict_invalid_parameters(self) -> None:
        """Test parsing dict with invalid parameters type."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {
            "tool": "create_ticket",
            "parameters": "invalid",  # Should be dict
        }

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is None

    def test_parse_tool_call_from_dict_unknown_tool(self) -> None:
        """Test parsing dict with unknown tool name."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {"tool": "unknown_tool", "parameters": {"title": "Test ticket"}}

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is None

    def test_parse_tool_call_from_dict_no_parameters(self) -> None:
        """Test parsing dict without parameters key."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_data: dict[str, Any] = {"tool": "create_ticket"}

        result = adapter._parse_tool_call_from_dict(tool_data)

        assert result is not None
        assert result.type == ToolCallType.CREATE_TICKET
        assert result.parameters == {}

    @pytest.mark.asyncio
    async def test_execute_tool_call_create_ticket_with_description(self) -> None:
        """Test executing create ticket with description."""
        mock_service = AsyncMock()
        mock_ticket = Ticket(
            id=uuid4(),
            title="Test ticket",
            description="Test description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test-user",
        )
        mock_service.create_ticket.return_value = mock_ticket

        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET,
            parameters={"title": "Test ticket", "description": "Test description", "priority": "high"},
        )

        result = await adapter._execute_tool_call(tool_call)

        assert result == mock_ticket
        mock_service.create_ticket.assert_called_once_with(
            title="Test ticket", description="Test description", priority=TicketPriority.HIGH, reporter="test-user"
        )

    @pytest.mark.asyncio
    async def test_execute_tool_call_create_ticket_default_description(self) -> None:
        """Test executing create ticket with default description."""
        mock_service = AsyncMock()
        mock_ticket = Ticket(
            id=uuid4(),
            title="Test ticket",
            description="",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user",
        )
        mock_service.create_ticket.return_value = mock_ticket

        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.CREATE_TICKET, parameters={"title": "Test ticket"})

        result = await adapter._execute_tool_call(tool_call)

        assert result == mock_ticket
        mock_service.create_ticket.assert_called_once_with(
            title="Test ticket", description="", priority=TicketPriority.MEDIUM, reporter="test-user"
        )

    @pytest.mark.asyncio
    async def test_execute_tool_call_list_tickets_with_status(self) -> None:
        """Test executing list tickets with status filter."""
        mock_service = AsyncMock()
        mock_tickets = [
            Ticket(
                id=uuid4(),
                title="Ticket 1",
                description="",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                reporter="test-user",
            )
        ]
        mock_service.list_tickets.return_value = mock_tickets

        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.LIST_TICKETS, parameters={"status": "open", "limit": 5})

        result = await adapter._execute_tool_call(tool_call)

        assert result == mock_tickets
        mock_service.list_tickets.assert_called_once_with(assignee="test-user", status=TicketStatus.OPEN, limit=5)

    @pytest.mark.asyncio
    async def test_execute_tool_call_list_tickets_no_status(self) -> None:
        """Test executing list tickets without status filter."""
        mock_service = AsyncMock()
        mock_tickets: list[Ticket] = []
        mock_service.list_tickets.return_value = mock_tickets

        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.LIST_TICKETS, parameters={})

        result = await adapter._execute_tool_call(tool_call)

        assert result == mock_tickets
        mock_service.list_tickets.assert_called_once_with(assignee="test-user", status=None, limit=10)

    @pytest.mark.asyncio
    async def test_execute_tool_call_get_ticket(self) -> None:
        """Test executing get ticket."""
        mock_service = AsyncMock()
        ticket_id = uuid4()
        mock_ticket = Ticket(
            id=ticket_id,
            title="Test ticket",
            description="",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user",
        )
        mock_service.get_ticket.return_value = mock_ticket

        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        tool_call = ToolCall(type=ToolCallType.GET_TICKET, parameters={"ticket_id": str(ticket_id)})

        result = await adapter._execute_tool_call(tool_call)

        assert result == mock_ticket
        mock_service.get_ticket.assert_called_once_with(ticket_id)

    @pytest.mark.asyncio
    async def test_execute_tool_call_unsupported_type(self) -> None:
        """Test executing unsupported tool type."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        # Create a mock tool call with an invalid type
        tool_call = MagicMock()
        tool_call.type = "INVALID_TYPE"

        with pytest.raises(ValueError, match="Unsupported tool type"):
            await adapter._execute_tool_call(tool_call)

    def test_format_success_message_create_ticket(self) -> None:
        """Test formatting success message for create ticket."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        mock_ticket = Ticket(
            id=uuid4(),
            title="Test ticket",
            description="",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user",
        )

        message = adapter._format_success_message(ToolCallType.CREATE_TICKET, mock_ticket)

        assert message == "Created ticket: Test ticket"

    def test_format_success_message_list_tickets(self) -> None:
        """Test formatting success message for list tickets."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        mock_tickets: list[Ticket] = [MagicMock(), MagicMock()]  # type: ignore[list-item]

        message = adapter._format_success_message(ToolCallType.LIST_TICKETS, mock_tickets)

        assert message == "Found 2 tickets"

    def test_format_success_message_get_ticket(self) -> None:
        """Test formatting success message for get ticket."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        mock_ticket = Ticket(
            id=uuid4(),
            title="Retrieved ticket",
            description="",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user",
        )

        message = adapter._format_success_message(ToolCallType.GET_TICKET, mock_ticket)

        assert message == "Retrieved ticket: Retrieved ticket"

    def test_format_success_message_fallback(self) -> None:
        """Test formatting success message fallback."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        # Use an invalid tool type to trigger fallback
        message = adapter._format_success_message(
            "INVALID_TYPE",  # type: ignore[arg-type]
            None,
        )

        assert message == "Operation completed successfully"

    def test_parse_response_to_dict_from_dict(self) -> None:
        """Test parsing response from dict."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        response = {"tool": "create_ticket", "parameters": {}}

        result = adapter._parse_response_to_dict(response)

        assert result == response

    def test_parse_response_to_dict_from_json_string(self) -> None:
        """Test parsing response from JSON string."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        response_dict = {"tool": "create_ticket", "parameters": {}}
        response = json.dumps(response_dict)

        result = adapter._parse_response_to_dict(response)

        assert result == response_dict

    def test_parse_response_to_dict_invalid_json(self) -> None:
        """Test parsing response from invalid JSON string."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        response = "invalid json"

        result = adapter._parse_response_to_dict(response)

        assert result is None

    def test_parse_response_to_dict_json_not_dict(self) -> None:
        """Test parsing response from JSON that's not a dict."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        response = json.dumps(["not", "a", "dict"])

        result = adapter._parse_response_to_dict(response)

        assert result is None

    def test_parse_response_to_dict_invalid_type(self) -> None:
        """Test parsing response from invalid type."""
        mock_service = MagicMock()
        adapter = BaseTicketAIAdapter(ticket_service=mock_service, user_id="test-user")

        response = 123  # Invalid type

        result = adapter._parse_response_to_dict(response)

        assert result is None
