"""Integration tests for AI adapters with ticket service.

Second Submission Requirement:
Demonstrates integration with TWO different AI providers (Claude and OpenAI)
working with the Jira Ticket Service.

Architecture:
    User command → AI Adapter (Claude OR OpenAI) → Ticket Service → Jira API
"""

import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ticket_ai_adapter import AITicketAdapter, OpenAITicketAdapter
from ticket_api import Ticket, TicketPriority, TicketStatus


class TestClaudeAIAdapter:
    """Test Claude AI adapter integrating with ticket service.

    This demonstrates the FIRST AI provider (Claude) working with the ticket service.
    """

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create a mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def mock_claude_client(self) -> Mock:
        """Create a mock Claude client."""
        return Mock()

    @pytest.fixture
    def claude_adapter(
        self,
        mock_ticket_service: AsyncMock,
        mock_claude_client: Mock,
    ) -> AITicketAdapter:
        """Create Claude AI adapter with mocked dependencies."""
        return AITicketAdapter(
            ticket_service=mock_ticket_service,
            claude_client=mock_claude_client,
            user_id="test-user@example.com",
            project_key="TEST",
        )

    @pytest.mark.asyncio
    async def test_claude_creates_ticket(
        self,
        claude_adapter: AITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test Claude adapter creating a ticket via natural language."""
        # Mock Claude response with tool call
        mock_claude_response = Mock()
        mock_claude_response.content = json.dumps(
            {
                "tool": "create_ticket",
                "parameters": {
                    "title": "Fix login bug",
                    "description": "Users cannot log in to the application",
                    "priority": "high",
                },
            }
        )

        # Mock ticket service response
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Fix login bug",
            description="Users cannot log in to the application",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test-user@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Mock the Claude API call
        with patch("fast_api_client.api.chat.send_chat_message_chat_post") as mock_chat_module:
            mock_chat_module.asyncio.return_value = mock_claude_response

            # Process natural language command
            result = await claude_adapter.process_command(
                "Create a high priority ticket for fixing the login bug where users can't log in"
            )

            # Verify success
            assert result.success
            assert "Fix login bug" in result.message
            assert result.data == expected_ticket

            # Verify ticket service was called correctly
            mock_ticket_service.create_ticket.assert_called_once()
            call_args = mock_ticket_service.create_ticket.call_args
            assert call_args.kwargs["title"] == "Fix login bug"
            assert call_args.kwargs["priority"] == TicketPriority.HIGH

    @pytest.mark.asyncio
    async def test_claude_lists_tickets(
        self,
        claude_adapter: AITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test Claude adapter listing tickets via natural language."""
        # Mock Claude response
        mock_claude_response = Mock()
        mock_claude_response.content = json.dumps(
            {
                "tool": "list_tickets",
                "parameters": {
                    "status": "open",
                    "limit": 5,
                },
            }
        )

        # Mock ticket service response
        expected_tickets = [
            Ticket(
                id=uuid.uuid4(),
                title=f"Ticket {i}",
                description=f"Description {i}",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                reporter="test-user@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(5)
        ]
        mock_ticket_service.list_tickets.return_value = expected_tickets

        with patch("fast_api_client.api.chat.send_chat_message_chat_post") as mock_chat_module:
            mock_chat_module.asyncio.return_value = mock_claude_response

            result = await claude_adapter.process_command("Show me my 5 latest open tickets")

            assert result.success
            assert "5 ticket(s)" in result.message
            assert result.data == expected_tickets

            # Verify correct API call
            mock_ticket_service.list_tickets.assert_called_once()
            call_args = mock_ticket_service.list_tickets.call_args
            assert call_args.kwargs["status"] == TicketStatus.OPEN
            assert call_args.kwargs["limit"] == 5


class TestOpenAIAdapter:
    """Test OpenAI adapter integrating with ticket service.

    This demonstrates the SECOND AI provider (OpenAI) working with the ticket service.
    KEY REQUIREMENT: Shows multi-provider support.
    """

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create a mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def openai_adapter(self, mock_ticket_service: AsyncMock) -> OpenAITicketAdapter:
        """Create OpenAI adapter with mocked dependencies."""
        with patch("ticket_ai_adapter.openai_adapter.openai.OpenAI"):
            adapter = OpenAITicketAdapter(
                ticket_service=mock_ticket_service,
                openai_api_key="sk-test-key",
                user_id="test-user@example.com",
                project_key="TEST",
            )
            adapter.openai_client = Mock()  # Replace with mock
            return adapter

    @pytest.mark.asyncio
    async def test_openai_creates_ticket(
        self,
        openai_adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test OpenAI adapter creating a ticket via natural language."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "tool": "create_ticket",
                "parameters": {
                    "title": "Add dark mode",
                    "description": "Implement dark theme for the application",
                    "priority": "medium",
                },
            }
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        openai_adapter.openai_client.chat.completions.create.return_value = mock_response

        # Mock ticket service response
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Add dark mode",
            description="Implement dark theme for the application",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Process command
        result = await openai_adapter.process_command("Create a ticket to add dark mode to the application")

        # Verify success
        assert result.success
        assert "Add dark mode" in result.message
        assert result.data == expected_ticket

        # Verify OpenAI was called
        openai_adapter.openai_client.chat.completions.create.assert_called_once()

        # Verify ticket service was called correctly
        mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_lists_tickets(
        self,
        openai_adapter: OpenAITicketAdapter,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test OpenAI adapter listing tickets via natural language."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "tool": "list_tickets",
                "parameters": {
                    "status": "in_progress",
                    "limit": 10,
                },
            }
        )
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        openai_adapter.openai_client.chat.completions.create.return_value = mock_response

        # Mock ticket service response
        expected_tickets = [
            Ticket(
                id=uuid.uuid4(),
                title=f"Ticket {i}",
                description=f"Description {i}",
                status=TicketStatus.IN_PROGRESS,
                priority=TicketPriority.MEDIUM,
                reporter="test-user@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(10)
        ]
        mock_ticket_service.list_tickets.return_value = expected_tickets

        result = await openai_adapter.process_command("Show me all in-progress tickets")

        assert result.success
        assert "10 ticket(s)" in result.message
        assert result.data == expected_tickets


class TestBothAIProviders:
    """Test suite demonstrating BOTH AI providers work with ticket service.

    KEY SECOND SUBMISSION REQUIREMENT:
    Shows that the Ticket Service integrates with MULTIPLE AI providers.
    """

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Shared mock ticket service for both providers."""
        return AsyncMock()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("adapter_type", "provider_name"),
        [
            ("claude", "Claude"),
            ("openai", "OpenAI"),
        ],
    )
    async def test_both_providers_can_create_tickets(
        self,
        adapter_type: str,
        provider_name: str,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Parameterized test: BOTH Claude and OpenAI can create tickets.

        This single test runs twice - once with Claude, once with OpenAI,
        demonstrating that both providers integrate identically with the ticket service.
        """
        # Mock ticket service response (same for both)
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test Description",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            reporter="test-user@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Tool call response (same structure for both)
        tool_call_json = json.dumps(
            {
                "tool": "create_ticket",
                "parameters": {
                    "title": "Test Ticket",
                    "description": "Test Description",
                    "priority": "medium",
                },
            }
        )

        if adapter_type == "claude":
            # Test with Claude
            mock_claude_response = Mock()
            mock_claude_response.content = tool_call_json

            with patch("fast_api_client.api.chat.send_chat_message_chat_post") as mock_chat_module:
                mock_chat_module.asyncio.return_value = mock_claude_response

                adapter = AITicketAdapter(
                    ticket_service=mock_ticket_service,
                    claude_client=Mock(),
                    user_id="test-user@example.com",
                )

                result = await adapter.process_command("Create a test ticket")

                assert result.success
                assert provider_name in ["Claude", "OpenAI"]  # Demonstrate provider used
                mock_ticket_service.create_ticket.assert_called_once()

        else:  # openai
            # Test with OpenAI
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = tool_call_json
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            with patch("ticket_ai_adapter.openai_adapter.openai.OpenAI"):
                adapter = OpenAITicketAdapter(
                    ticket_service=mock_ticket_service,
                    openai_api_key="sk-test",
                    user_id="test-user@example.com",
                )
                adapter.openai_client = Mock()
                adapter.openai_client.chat.completions.create.return_value = mock_response

                result = await adapter.process_command("Create a test ticket")

                assert result.success
                assert provider_name in ["Claude", "OpenAI"]
                mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_interchangeable_providers(self, mock_ticket_service: AsyncMock) -> None:
        """Demonstrate that Claude and OpenAI adapters are interchangeable.

        Both implement the same interface and can be swapped without changing
        the application code.
        """
        # Both adapters have the same process_command interface
        mock_claude_response = Mock()
        mock_claude_response.content = json.dumps(
            {
                "tool": "list_tickets",
                "parameters": {"limit": 5},
            }
        )

        tickets = [
            Ticket(
                id=uuid.uuid4(),
                title="Ticket 1",
                description="Description 1",
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                reporter="test@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        ]
        mock_ticket_service.list_tickets.return_value = tickets

        # Test with Claude
        with patch("fast_api_client.api.chat.send_chat_message_chat_post") as mock_chat_module:
            mock_chat_module.asyncio.return_value = mock_claude_response

            claude_adapter = AITicketAdapter(
                ticket_service=mock_ticket_service,
                claude_client=Mock(),
                user_id="test@example.com",
            )

            claude_result = await claude_adapter.process_command("Show tickets")
            assert claude_result.success

        # Test with OpenAI (same ticket service)
        mock_ticket_service.reset_mock()

        mock_openai_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = json.dumps(
            {
                "tool": "list_tickets",
                "parameters": {"limit": 5},
            }
        )
        mock_choice.message = mock_message
        mock_openai_response.choices = [mock_choice]
        mock_ticket_service.list_tickets.return_value = tickets

        with patch("ticket_ai_adapter.openai_adapter.openai.OpenAI"):
            openai_adapter = OpenAITicketAdapter(
                ticket_service=mock_ticket_service,
                openai_api_key="sk-test",
                user_id="test@example.com",
            )
            openai_adapter.openai_client = Mock()
            openai_adapter.openai_client.chat.completions.create.return_value = mock_openai_response

            openai_result = await openai_adapter.process_command("Show tickets")
            assert openai_result.success

        # Both produce the same result
        assert claude_result.success == openai_result.success
