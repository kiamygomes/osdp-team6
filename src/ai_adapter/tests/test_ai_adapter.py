# /Users/Mikiyas/Desktop/Open_Source/osdp-team6/src/ai_adapter/tests/test_adapter.py
"""Tests for the AITicketAdapter class."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from ticket_api import Ticket, TicketPriority, TicketStatus

from ticket_ai_adapter import AITicketAdapter, ToolCallType
from ticket_ai_adapter.models import ToolCall


@pytest.fixture
def mock_ticket_service() -> Mock:
    """Create a mock ticket service."""
    service = Mock()
    service.create_ticket = AsyncMock()
    service.get_ticket = AsyncMock()
    service.list_tickets = AsyncMock()
    service.update_ticket = AsyncMock()
    service.add_comment = AsyncMock()
    service.transition_status = AsyncMock()
    service.reassign_ticket = AsyncMock()
    return service


@pytest.fixture
def mock_claude_client() -> Mock:
    """Create a mock Claude client."""
    return Mock()


@pytest.fixture
def adapter(mock_ticket_service: Mock, mock_claude_client: Mock) -> AITicketAdapter:
    """Create an AITicketAdapter instance."""
    return AITicketAdapter(
        ticket_service=mock_ticket_service,
        claude_client=mock_claude_client,
        user_id="test-user@example.com",
        project_key="TEST",
    )


def test_parse_tool_call_create_ticket(adapter: AITicketAdapter) -> None:
    """Test parsing a create_ticket tool call from AI response."""
    response = Mock()
    response.content = json.dumps(
        {
            "tool": "create_ticket",
            "parameters": {
                "title": "Fix login bug",
                "description": "Users cannot log in",
                "priority": "high",
            },
        }
    )

    tool_call = adapter._parse_tool_call(response)

    assert tool_call is not None
    assert tool_call.type == ToolCallType.CREATE_TICKET
    assert tool_call.parameters["title"] == "Fix login bug"
    assert tool_call.parameters["description"] == "Users cannot log in"
    assert tool_call.parameters["priority"] == "high"


def test_parse_tool_call_no_tool(adapter: AITicketAdapter) -> None:
    """Test parsing a response with no tool call."""
    response = Mock()
    response.content = (
        "I need more information about the bug. "
        "Can you describe what happens when users try to log in?"
    )

    tool_call = adapter._parse_tool_call(response)

    assert tool_call is None


def test_parse_tool_call_invalid_json(adapter: AITicketAdapter) -> None:
    """Test parsing a response with invalid JSON."""
    response = Mock()
    response.content = '{"tool": "create_ticket", invalid json}'

    tool_call = adapter._parse_tool_call(response)

    assert tool_call is None


@pytest.mark.asyncio
async def test_execute_tool_call_create_ticket(
    adapter: AITicketAdapter, mock_ticket_service: Mock
) -> None:
    """Test executing a create_ticket tool call."""
    ticket_id = uuid4()
    expected_ticket = Ticket(
        id=ticket_id,
        title="Fix login bug",
        description="Users cannot log in",
        reporter="test-user@example.com",
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
    )
    mock_ticket_service.create_ticket.return_value = expected_ticket

    tool_call = ToolCall(
        type=ToolCallType.CREATE_TICKET,
        parameters={
            "title": "Fix login bug",
            "description": "Users cannot log in",
            "priority": "high",
        },
    )

    result = await adapter._execute_tool_call(tool_call)

    assert result == expected_ticket
    mock_ticket_service.create_ticket.assert_called_once_with(
        title="Fix login bug",
        description="Users cannot log in",
        reporter="test-user@example.com",
        priority=TicketPriority.HIGH,
        assignee=None,
    )


@pytest.mark.asyncio
async def test_execute_tool_call_list_tickets(
    adapter: AITicketAdapter, mock_ticket_service: Mock
) -> None:
    """Test executing a list_tickets tool call."""
    expected_tickets = [
        Ticket(
            id=uuid4(),
            title="Bug 1",
            description="Description 1",
            reporter="user1",
            status=TicketStatus.OPEN,
        ),
        Ticket(
            id=uuid4(),
            title="Bug 2",
            description="Description 2",
            reporter="user2",
            status=TicketStatus.OPEN,
        ),
    ]
    mock_ticket_service.list_tickets.return_value = expected_tickets

    tool_call = ToolCall(type=ToolCallType.LIST_TICKETS, parameters={"status": "open", "limit": 10})

    result = await adapter._execute_tool_call(tool_call)

    assert result == expected_tickets
    mock_ticket_service.list_tickets.assert_called_once_with(
        status=TicketStatus.OPEN,
        assignee=None,
        limit=10,
    )


def test_format_success_message_create_ticket(adapter: AITicketAdapter) -> None:
    """Test formatting success message for ticket creation."""
    ticket = Ticket(
        id=uuid4(),
        title="Fix login bug",
        description="Users cannot log in",
        reporter="test-user",
        status=TicketStatus.OPEN,
    )

    message = adapter._format_success_message(ToolCallType.CREATE_TICKET, ticket)

    assert "Successfully created ticket" in message
    assert "Fix login bug" in message


def test_format_success_message_list_tickets(adapter: AITicketAdapter) -> None:
    """Test formatting success message for listing tickets."""
    tickets = [Mock(), Mock(), Mock()]

    message = adapter._format_success_message(ToolCallType.LIST_TICKETS, tickets)

    assert "Found 3 ticket(s)" in message
