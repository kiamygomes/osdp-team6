"""Main Application Orchestrator - HW3 Final Submission.

This module serves as the main controller that orchestrates the complete
Chat → AI → Tickets pipeline as required by HW3.

User Flow:
1. User types command in Chat interface
2. Chat sends text to AI Service
3. AI analyzes text and returns structured tool call
4. Application executes tool call against Ticket Service
5. Ticket Service confirms action
6. Chat relays success message back to user

Architecture:
- Uses local modules directly (not HTTP adapters) as suggested by TA feedback
- Integrates: Chat (Slack team), AI (Claude/OpenAI teams), Tickets (our team)
- Provides both CLI demo and importable orchestrator class
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol

# AI adapters from our team that integrate with other teams' AI services
from ticket_ai_adapter.team_integration import ClaudeTeamAdapter, OpenAITeamAdapter

# Local team modules (direct integration, no HTTP needed per TA feedback)
from ticket_impl import TicketImpl


# Chat integration protocol - defines the interface we expect from chat clients
class ChatClientProtocol(Protocol):
    """Protocol defining the chat client interface."""

    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a message to a channel."""
        ...

    def get_messages(self, channel_id: str, limit: int = 10) -> list[Any]:
        """Get messages from a channel."""
        ...


# Try to import actual chat implementation
CHAT_AVAILABLE = False
try:
    from chat_api.chat_api import ChatInterface as _ChatInterface
    from chat_api.chat_api import Message as _Message

    CHAT_AVAILABLE = True
    logger_chat = logging.getLogger(__name__ + ".chat")
    logger_chat.info("Chat API loaded successfully")
except ImportError:
    _ChatInterface = None  # type: ignore[assignment, misc]
    _Message = None  # type: ignore[assignment, misc]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TicketBotOrchestrator:
    """Main orchestrator for the Chat → AI → Tickets pipeline.

    This class coordinates the three verticals:
    - Chat: Receives user commands (Slack team's module)
    - AI: Processes natural language (Claude/OpenAI teams' modules)
    - Tickets: Manages work items (our Jira integration)
    """

    user_id: str
    project_key: str
    ticket_service: TicketImpl
    ai_adapter: ClaudeTeamAdapter | OpenAITeamAdapter
    chat_client: ChatClientProtocol | None

    def __init__(
        self,
        user_id: str,
        project_key: str,
        ai_provider: str = "claude",
        chat_client: ChatClientProtocol | None = None,
    ) -> None:
        """Initialize the orchestrator with all required services.

        Args:
            user_id: User ID for ticket operations
            project_key: Jira project key
            ai_provider: Which AI provider to use ("claude" or "openai")
            chat_client: Optional ChatInterface implementation (Slack team's module)

        """
        self.user_id = user_id
        self.project_key = project_key
        self.chat_client = chat_client

        # Initialize ticket service (our team's implementation)
        self.ticket_service = TicketImpl(
            user_id=user_id,
            project_key=project_key,
        )

        # Initialize AI adapter based on provider choice
        if ai_provider == "claude":
            self.ai_adapter = ClaudeTeamAdapter(
                ticket_service=self.ticket_service,
                user_id=user_id,
                project_key=project_key,
            )
            logger.info("Initialized with Claude team's AI service")
        elif ai_provider == "openai":
            self.ai_adapter = OpenAITeamAdapter(
                ticket_service=self.ticket_service,
                user_id=user_id,
                project_key=project_key,
            )
            logger.info("Initialized with OpenAI team's AI service")
        else:
            msg = f"Unknown AI provider: {ai_provider}"
            raise ValueError(msg)

        logger.info(
            "TicketBotOrchestrator initialized for user=%s, project=%s, ai=%s, chat=%s",
            user_id,
            project_key,
            ai_provider,
            "enabled" if chat_client else "simulated",
        )

    async def process_chat_message(
        self,
        message: str,
        channel_id: str | None = None,
    ) -> dict[str, Any]:
        """Process a chat message through the complete pipeline.

        This is the main entry point that implements the HW3 user flow:
        Chat → AI → Tickets → Response

        Args:
            message: Natural language message from chat
            channel_id: Optional chat channel ID (for future chat integration)

        Returns:
            Dictionary with processing result:
            {
                "success": bool,
                "message": str,
                "data": Any (ticket data if successful),
                "error": str (if failed)
            }

        Example:
            >>> orchestrator = TicketBotOrchestrator("user1", "OSDP")
            >>> result = await orchestrator.process_chat_message(
            ...     "Create a ticket for fixing the login bug"
            ... )
            >>> print(result["message"])
            "Successfully created ticket: Fix login bug (ID: ...)"

        """
        logger.info("Processing chat message: %s", message)

        try:
            # Step 1-4: AI analyzes message and executes ticket operation
            result = await self.ai_adapter.process_command(message)
        except Exception as e:
            logger.exception("Unexpected error in orchestrator")
            return {
                "success": False,
                "message": "An unexpected error occurred",
                "data": None,
                "error": str(e),
                "channel_id": channel_id,
            }
        else:
            # Step 5-6: Format response for chat
            if result.success:
                logger.info("Successfully processed: %s", result.message)
            else:
                logger.error("Failed to process: %s", result.error)

            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "error": result.error,
                "channel_id": channel_id,
            }

    async def send_to_chat(
        self,
        channel_id: str,
        message: str,
    ) -> bool:
        """Send a message to chat channel.

        Uses the Slack team's ChatInterface if available, otherwise logs the message.

        Args:
            channel_id: Chat channel identifier
            message: Message to send

        Returns:
            True if sent successfully

        """
        if self.chat_client is not None:
            try:
                # Use actual chat client if available
                result = self.chat_client.send_message(channel_id, message)
                logger.info("Sent to channel %s via ChatInterface", channel_id)
            except Exception:
                logger.exception("Failed to send to chat")
                return False
            else:
                return bool(result)
        # Simulate sending when chat client not available
        logger.info("[SIMULATED] Would send to channel %s: %s", channel_id, message)
        return True

    async def process_incoming_chat(
        self,
        channel_id: str,
        command_prefix: str = "!ticket",
    ) -> int:
        """Process incoming messages from a chat channel.

        Implements the full bidirectional Chat ↔ AI ↔ Tickets flow:
        1. Gets new messages from chat (using ChatInterface.get_messages)
        2. Processes each message through AI and Tickets
        3. Sends responses back to chat

        Args:
            channel_id: Chat channel to monitor
            command_prefix: Prefix to identify bot commands (default: "!ticket")

        Returns:
            Number of messages processed

        """
        if self.chat_client is None:
            logger.warning("Chat client not available - cannot process incoming messages")
            return 0

        try:
            # Get new messages from chat
            messages = self.chat_client.get_messages(channel_id, limit=10)
            processed_count = 0

            for msg in messages:
                # Only process messages with the command prefix
                if not msg.content.startswith(command_prefix):
                    continue

                logger.info("Processing message from %s: %s", msg.sender_id, msg.content)

                # Remove prefix from command
                command = msg.content[len(command_prefix) :].strip()

                # Process through AI → Tickets pipeline
                result = await self.process_chat_message(
                    message=command,
                    channel_id=channel_id,
                )

                # Send response back to chat
                await self.send_to_chat(channel_id, result["message"])
                processed_count += 1

            logger.info("Processed %d messages from channel %s", processed_count, channel_id)
        except Exception:
            logger.exception("Error processing incoming chat messages")
            return 0
        else:
            return processed_count


async def demo_cli() -> None:
    """Demo CLI showing the complete pipeline in action.

    This demonstrates:
    1. User typing commands
    2. AI processing with provider swapping
    3. Ticket operations
    4. Response messages
    """
    # Demo with Claude AI provider
    orchestrator_claude = TicketBotOrchestrator(
        user_id="test-demo-user",
        project_key="DEMO",
        ai_provider="claude",
    )

    # Example 1: Create a ticket
    user_message = "Create a ticket for fixing the login bug with high priority"

    await orchestrator_claude.process_chat_message(user_message)

    # Example 2: List tickets
    user_message = "Show me all open tickets"

    await orchestrator_claude.process_chat_message(user_message)

    # Demo with OpenAI provider
    orchestrator_openai = TicketBotOrchestrator(
        user_id="test-demo-user",
        project_key="DEMO",
        ai_provider="openai",
    )

    user_message = "Create a ticket for updating documentation"

    await orchestrator_openai.process_chat_message(user_message)


def main() -> None:
    """Run the main application entry point."""
    asyncio.run(demo_cli())


if __name__ == "__main__":
    main()
