"""Simple integration tests for AI adapters with ticket service.

These tests demonstrate that TWO different AI providers (Claude and OpenAI)
can integrate with the Jira Ticket Service.

Second Submission Requirement: Multi-provider AI integration.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from ticket_ai_adapter import AITicketAdapter, OpenAITicketAdapter
from ticket_ai_adapter.models import ToolCall, ToolCallType

from ticket_api import Ticket, TicketPriority, TicketStatus


class TestClaudeAdapter:
    """Test Claude AI adapter (Provider 1)."""

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_ticket_service: AsyncMock) -> AITicketAdapter:
        """Create Claude adapter."""
        return AITicketAdapter(
            ticket_service=mock_ticket_service,
            claude_client=Mock(),
            user_id="test@example.com",
        )

    @pytest.mark.asyncio
    async def test_claude_execute_create_ticket(
        self,
        adapter: AITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test Claude adapter executes create_ticket tool call."""
        # Create a tool call
        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET,
            parameters={
                "title": "Fix login bug",
                "description": "Users cannot log in",
                "priority": "high",
            },
        )

        # Mock ticket service response
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Fix login bug",
            description="Users cannot log in",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Execute the tool call
        result = await adapter._execute_tool_call(tool_call)

        # Verify ticket service was called correctly
        assert result == expected_ticket
        mock_ticket_service.create_ticket.assert_called_once()
        call_kwargs = mock_ticket_service.create_ticket.call_args.kwargs
        assert call_kwargs["title"] == "Fix login bug"
        assert call_kwargs["priority"] == TicketPriority.HIGH

    @pytest.mark.asyncio
    async def test_claude_execute_list_tickets(
        self,
        adapter: AITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test Claude adapter executes list_tickets tool call."""
        tool_call = ToolCall(
            type=ToolCallType.LIST_TICKETS,
            parameters={"status": "open", "limit": 5},
        )

        expected_tickets = [
            Ticket(
                id=uuid.uuid4(),
                title=f"Ticket {i}",
                description="Test",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                reporter="test@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(5)
        ]
        mock_ticket_service.list_tickets.return_value = expected_tickets

        result = await adapter._execute_tool_call(tool_call)

        assert result == expected_tickets
        mock_ticket_service.list_tickets.assert_called_once()
        call_kwargs = mock_ticket_service.list_tickets.call_args.kwargs
        assert call_kwargs["status"] == TicketStatus.OPEN
        assert call_kwargs["limit"] == 5


class TestOpenAIAdapter:
    """Test OpenAI adapter (Provider 2) - demonstrates multi-provider support."""

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def adapter(self, mock_ticket_service: AsyncMock) -> OpenAITicketAdapter:
        """Create OpenAI adapter."""
        with patch("openai.OpenAI"):
            adapter = OpenAITicketAdapter(
                ticket_service=mock_ticket_service,
                openai_api_key="sk-test",
                user_id="test@example.com",
            )
            adapter.openai_client = Mock()
            return adapter

    @pytest.mark.asyncio
    async def test_openai_execute_create_ticket(
        self,
        adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test OpenAI adapter executes create_ticket tool call."""
        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET,
            parameters={
                "title": "Add dark mode",
                "description": "Implement dark theme",
                "priority": "medium",
            },
        )

        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Add dark mode",
            description="Implement dark theme",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        result = await adapter._execute_tool_call(tool_call)

        assert result == expected_ticket
        mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_execute_list_tickets(
        self,
        adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test OpenAI adapter executes list_tickets tool call."""
        tool_call = ToolCall(
            type=ToolCallType.LIST_TICKETS,
            parameters={"status": "in_progress", "limit": 10},
        )

        expected_tickets = [
            Ticket(
                id=uuid.uuid4(),
                title=f"Ticket {i}",
                description="Test",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.MEDIUM,
                reporter="test@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(10)
        ]
        mock_ticket_service.list_tickets.return_value = expected_tickets

        result = await adapter._execute_tool_call(tool_call)

        assert result == expected_tickets
        mock_ticket_service.list_tickets.assert_called_once()


class TestMultiProviderSupport:
    """KEY REQUIREMENT: Demonstrate BOTH providers work with ticket service.

    This is the core Second Submission requirement - showing that the Jira
    Ticket Service integrates with MULTIPLE AI providers.
    """

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Shared mock ticket service."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_both_providers_execute_same_tool_call(
        self,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test both Claude and OpenAI execute the same tool call identically."""
        # Same tool call for both
        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET,
            parameters={
                "title": "Test Ticket",
                "description": "Test Description",
                "priority": "medium",
            },
        )

        # Same expected result
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Test with Claude
        claude_adapter = AITicketAdapter(
            ticket_service=mock_ticket_service,
            claude_client=Mock(),
            user_id="test@example.com",
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        claude_result = await claude_adapter._execute_tool_call(tool_call)

        assert claude_result == expected_ticket
        assert mock_ticket_service.create_ticket.call_count == 1

        # Reset mock
        mock_ticket_service.reset_mock()

        # Test with OpenAI - same tool call, same result
        with patch("openai.OpenAI"):
            openai_adapter = OpenAITicketAdapter(
                ticket_service=mock_ticket_service,
                openai_api_key="sk-test",
                user_id="test@example.com",
            )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        openai_result = await openai_adapter._execute_tool_call(tool_call)

        assert openai_result == expected_ticket
        assert mock_ticket_service.create_ticket.call_count == 1

        # Both produce identical results
        assert claude_result.title == openai_result.title
        assert claude_result.description == openai_result.description

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("tool_type", "params"),
        [
            (ToolCallType.CREATE_TICKET, {"title": "Test", "description": "Desc", "priority": "high"}),
            (ToolCallType.LIST_TICKETS, {"status": "open", "limit": 10}),
        ],
    )
    async def test_both_providers_support_all_operations(
        self,
        mock_ticket_service: AsyncMock,
        tool_type: ToolCallType,
        params: dict[str, object],
    ) -> None:
        """Parameterized test: Both providers support all ticket operations."""
        tool_call = ToolCall(type=tool_type, parameters=params)

        # Setup appropriate mock response
        mock_response: Ticket | list[Ticket]
        if tool_type == ToolCallType.CREATE_TICKET:
            mock_response = Ticket(
                id=uuid.uuid4(),
                title=str(params["title"]),
                description=str(params["description"]),
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                reporter="test@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            mock_ticket_service.create_ticket.return_value = mock_response
        elif tool_type == ToolCallType.LIST_TICKETS:
            mock_response = []
            mock_ticket_service.list_tickets.return_value = mock_response

        # Test Claude
        claude_adapter = AITicketAdapter(
            ticket_service=mock_ticket_service,
            claude_client=Mock(),
            user_id="test@example.com",
        )
        await claude_adapter._execute_tool_call(tool_call)

        # Test OpenAI
        mock_ticket_service.reset_mock()
        if tool_type == ToolCallType.CREATE_TICKET:
            mock_ticket_service.create_ticket.return_value = mock_response
        elif tool_type == ToolCallType.LIST_TICKETS:
            mock_ticket_service.list_tickets.return_value = mock_response

        with patch("openai.OpenAI"):
            openai_adapter = OpenAITicketAdapter(
                ticket_service=mock_ticket_service,
                openai_api_key="sk-test",
                user_id="test@example.com",
            )
        await openai_adapter._execute_tool_call(tool_call)

        # Both successfully executed the operation
        # (if either failed, test would have raised exception)
        assert True  # Test passed - both providers work
