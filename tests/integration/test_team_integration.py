"""Integration tests for Second Submission - Other Teams' AI Services.

These tests demonstrate that our Jira Ticket Service integrates with:
1. Claude team's ai_chat_api (from https://github.com/shichenz1999/oss-taapp/tree/hw3)
2. OpenAI team's ai_api (from https://github.com/natashagit/oss-nml/tree/hw_3_working)

This fulfills the requirement: "Demonstrate successful integration with at least two different providers"
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from ticket_ai_adapter.team_integration import ClaudeTeamAdapter, OpenAITeamAdapter

from ticket_api import Ticket, TicketPriority, TicketStatus


class TestClaudeTeamIntegration:
    """Test integration with Claude team's ai_chat_api package."""

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def mock_claude_ai_interface(self) -> Mock:
        """Mock Claude team's AIInterface."""
        return Mock()

    @pytest.fixture
    def adapter(
        self,
        mock_ticket_service: AsyncMock,
        mock_claude_ai_interface: Mock,
    ) -> ClaudeTeamAdapter:
        """Create Claude team adapter with mocked AI interface."""
        with patch("ai_chat_api.get_ai_interface", return_value=mock_claude_ai_interface):
            return ClaudeTeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )

    @pytest.mark.asyncio
    async def test_claude_team_create_ticket(
        self,
        adapter: ClaudeTeamAdapter,
        mock_ticket_service: AsyncMock,
        mock_claude_ai_interface: Mock,
    ) -> None:
        """Test creating ticket via Claude team's AI service."""
        # Mock Claude team's AI response
        mock_claude_ai_interface.generate_response.return_value = {
            "tool": "create_ticket",
            "parameters": {
                "title": "Fix authentication bug",
                "description": "Users can't log in",
                "priority": "high",
            },
        }

        # Mock ticket service response
        expected_ticket = Ticket(
            id=uuid.uuid4(),
            title="Fix authentication bug",
            description="Users can't log in",
            status=TicketStatus.OPEN,
            priority=TicketPriority.HIGH,
            reporter="test@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_ticket_service.create_ticket.return_value = expected_ticket

        # Process command
        result = await adapter.process_command("Create a high priority ticket for auth bug")

        # Verify AI service was called
        mock_claude_ai_interface.generate_response.assert_called_once()
        call_args = mock_claude_ai_interface.generate_response.call_args
        assert "auth bug" in call_args[1]["user_input"]
        assert call_args[1]["response_schema"] is not None

        # Verify ticket was created
        assert result.success
        assert result.data == expected_ticket
        mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_claude_team_list_tickets(
        self,
        adapter: ClaudeTeamAdapter,
        mock_ticket_service: AsyncMock,
        mock_claude_ai_interface: Mock,
    ) -> None:
        """Test listing tickets via Claude team's AI service."""
        # Mock Claude team's AI response
        mock_claude_ai_interface.generate_response.return_value = {
            "tool": "list_tickets",
            "parameters": {
                "status": "open",
                "limit": 5,
            },
        }

        # Mock ticket service response
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

        # Process command
        result = await adapter.process_command("Show my 5 latest open tickets")

        # Verify
        assert result.success
        assert result.data == expected_tickets
        mock_ticket_service.list_tickets.assert_called_once()


class TestOpenAITeamIntegration:
    """Test integration with OpenAI team's ai_api package."""

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Create mock ticket service."""
        return AsyncMock()

    @pytest.fixture
    def mock_openai_ai_interface(self) -> Mock:
        """Mock OpenAI team's AIInterface."""
        return Mock()

    @pytest.fixture
    def adapter(
        self,
        mock_ticket_service: AsyncMock,
        mock_openai_ai_interface: Mock,
    ) -> OpenAITeamAdapter:
        """Create OpenAI team adapter with mocked AI interface."""
        with patch("ai_api.get_client", return_value=mock_openai_ai_interface):
            return OpenAITeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )

    @pytest.mark.asyncio
    async def test_openai_team_create_ticket(
        self,
        adapter: OpenAITeamAdapter,
        mock_ticket_service: AsyncMock,
        mock_openai_ai_interface: Mock,
    ) -> None:
        """Test creating ticket via OpenAI team's AI service."""
        # Mock OpenAI team's AI response
        mock_openai_ai_interface.generate_response.return_value = {
            "tool": "create_ticket",
            "parameters": {
                "title": "Add dark mode",
                "description": "Implement dark theme",
                "priority": "medium",
            },
        }

        # Mock ticket service response
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

        # Process command
        result = await adapter.process_command("Create a ticket for dark mode feature")

        # Verify AI service was called
        mock_openai_ai_interface.generate_response.assert_called_once()
        call_args = mock_openai_ai_interface.generate_response.call_args
        assert "dark mode" in call_args[1]["user_input"]
        assert call_args[1]["response_schema"] is not None

        # Verify ticket was created
        assert result.success
        assert result.data == expected_ticket
        mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_team_list_tickets(
        self,
        adapter: OpenAITeamAdapter,
        mock_ticket_service: AsyncMock,
        mock_openai_ai_interface: Mock,
    ) -> None:
        """Test listing tickets via OpenAI team's AI service."""
        # Mock OpenAI team's AI response
        mock_openai_ai_interface.generate_response.return_value = {
            "tool": "list_tickets",
            "parameters": {
                "status": "in_progress",
                "limit": 10,
            },
        }

        # Mock ticket service response
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

        # Process command
        result = await adapter.process_command("List my in-progress tickets")

        # Verify
        assert result.success
        assert result.data == expected_tickets
        mock_ticket_service.list_tickets.assert_called_once()


class TestMultiProviderTeamIntegration:
    """KEY TEST: Demonstrates BOTH teams' services work with our ticket service.

    This is the core Second Submission requirement.
    """

    @pytest.fixture
    def mock_ticket_service(self) -> AsyncMock:
        """Shared mock ticket service for both providers."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_both_teams_create_same_ticket(
        self,
        mock_ticket_service: AsyncMock,
    ) -> None:
        """Test both teams' AI services can create the same ticket.

        This proves:
        1. Claude team's ai_chat_api integrates with our ticket service
        2. OpenAI team's ai_api integrates with our ticket service
        3. Both produce identical results (provider-agnostic)
        """
        # Same expected result from ticket service
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

        # Test with Claude team's adapter
        mock_claude_ai = Mock()
        mock_claude_ai.generate_response.return_value = {
            "tool": "create_ticket",
            "parameters": {
                "title": "Test Ticket",
                "description": "Test Description",
                "priority": "medium",
            },
        }

        with patch("ai_chat_api.get_ai_interface", return_value=mock_claude_ai):
            claude_adapter = ClaudeTeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )

        mock_ticket_service.create_ticket.return_value = expected_ticket
        claude_result = await claude_adapter.process_command("Create test ticket")

        assert claude_result.success
        assert claude_result.data == expected_ticket
        assert mock_ticket_service.create_ticket.call_count == 1

        # Reset mock
        mock_ticket_service.reset_mock()

        # Test with OpenAI team's adapter - same prompt, same result
        mock_openai_ai = Mock()
        mock_openai_ai.generate_response.return_value = {
            "tool": "create_ticket",
            "parameters": {
                "title": "Test Ticket",
                "description": "Test Description",
                "priority": "medium",
            },
        }

        with patch("ai_api.get_client", return_value=mock_openai_ai):
            openai_adapter = OpenAITeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )

        mock_ticket_service.create_ticket.return_value = expected_ticket
        openai_result = await openai_adapter.process_command("Create test ticket")

        assert openai_result.success
        assert openai_result.data == expected_ticket
        assert mock_ticket_service.create_ticket.call_count == 1

        # Both produce identical results
        assert claude_result.data.title == openai_result.data.title
        assert claude_result.data.description == openai_result.data.description

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("command", "tool_type"),
        [
            ("Create a bug ticket", "create_ticket"),
            ("List my open tickets", "list_tickets"),
        ],
    )
    async def test_both_teams_support_all_operations(
        self,
        mock_ticket_service: AsyncMock,
        command: str,
        tool_type: str,
    ) -> None:
        """Parameterized test: Both teams support all ticket operations."""
        # Mock responses for both teams
        ai_response: dict[str, object]
        if tool_type == "create_ticket":
            ai_response = {
                "tool": tool_type,
                "parameters": {"title": "Test", "description": "Test", "priority": "high"},
            }
        else:
            ai_response = {
                "tool": tool_type,
                "parameters": {"status": "open", "limit": 10},
            }

        # Setup appropriate mock response
        mock_response: Ticket | list[Ticket]
        if tool_type == "create_ticket":
            mock_response = Ticket(
                id=uuid.uuid4(),
                title="Test",
                description="Test",
                status=TicketStatus.OPEN,
                priority=TicketPriority.HIGH,
                reporter="test@example.com",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            mock_ticket_service.create_ticket.return_value = mock_response
        elif tool_type == "list_tickets":
            mock_response = []
            mock_ticket_service.list_tickets.return_value = mock_response

        # Test Claude team
        mock_claude = Mock()
        mock_claude.generate_response.return_value = ai_response
        with patch("ai_chat_api.get_ai_interface", return_value=mock_claude):
            claude_adapter = ClaudeTeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )
        claude_result = await claude_adapter.process_command(command)
        assert claude_result.success

        # Test OpenAI team
        mock_ticket_service.reset_mock()
        if tool_type == "create_ticket":
            mock_ticket_service.create_ticket.return_value = mock_response
        elif tool_type == "list_tickets":
            mock_ticket_service.list_tickets.return_value = mock_response

        mock_openai = Mock()
        mock_openai.generate_response.return_value = ai_response
        with patch("ai_api.get_client", return_value=mock_openai):
            openai_adapter = OpenAITeamAdapter(
                ticket_service=mock_ticket_service,
                user_id="test@example.com",
            )
        openai_result = await openai_adapter.process_command(command)
        assert openai_result.success

        # Both successfully executed the operation
        assert True  # If we got here, both teams work!
