#!/usr/bin/env python3
"""Complete End-to-End Workflow Demo: OAuth → Chat → AI → Tickets.

This demo script showcases the complete HW3 integration:
1. OAuth authentication with Jira
2. Chat interface setup (Slack team)
3. AI processing (Claude/OpenAI teams)
4. Ticket operations (our team)
5. Complete bidirectional flow

Run this script to see the full pipeline in action.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main_app import CHAT_AVAILABLE, TicketBotOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_section(title: str) -> None:
    """Print a formatted section header."""


async def demo_oauth_flow() -> None:
    """Demonstrate OAuth authentication flow.

    Note: This requires actual Jira OAuth credentials.
    For demo purposes, we'll use a test user.
    """
    print_section("Step 1: OAuth Authentication")


async def demo_chat_integration() -> None:
    """Demonstrate chat integration with Slack team's module."""
    print_section("Step 2: Chat Interface Setup")

    if CHAT_AVAILABLE:
        pass
    else:
        pass


async def demo_ai_processing() -> None:
    """Demonstrate AI service integration."""
    print_section("Step 3: AI Service Integration")


async def demo_ticket_operations() -> None:
    """Demonstrate ticket service operations."""
    print_section("Step 4: Ticket Service Operations")


async def demo_complete_pipeline() -> None:
    """Demonstrate the complete Chat → AI → Tickets pipeline."""
    print_section("Step 5: Complete Pipeline Demo")

    # Initialize with Claude provider
    orchestrator = TicketBotOrchestrator(
        user_id="test-demo-user",
        project_key="DEMO",
        ai_provider="claude",
    )

    # Demo scenarios
    scenarios = [
        {
            "user": "Alice",
            "message": "Create a ticket for fixing the login bug with high priority",
            "description": "User wants to create a high-priority ticket",
        },
        {
            "user": "Bob",
            "message": "Show me all my open tickets",
            "description": "User wants to list their tickets",
        },
        {
            "user": "Charlie",
            "message": "Update ticket status to in progress for the login bug",
            "description": "User wants to transition ticket status",
        },
    ]

    for _i, scenario in enumerate(scenarios, 1):
        # Process the message - errors are expected without real backends
        try:
            await orchestrator.process_chat_message(
                message=scenario["message"],
                channel_id=f"demo-channel-{scenario['user'].lower()}",
            )
        except (ValueError, RuntimeError, ConnectionError) as e:
            # Expected errors in demo mode without real backends
            logger.debug("Demo scenario encountered expected error: %s", type(e).__name__)


async def demo_provider_switching() -> None:
    """Demonstrate switching between AI providers."""
    print_section("Step 6: AI Provider Switching")

    # Claude provider
    TicketBotOrchestrator(
        user_id="test-user",
        project_key="DEMO",
        ai_provider="claude",
    )

    # OpenAI provider
    TicketBotOrchestrator(
        user_id="test-user",
        project_key="DEMO",
        ai_provider="openai",
    )


async def demo_observability() -> None:
    """Demonstrate observability and monitoring."""
    print_section("Step 7: Observability & Monitoring")


async def main() -> None:
    """Run the complete demo."""
    input()

    try:
        await demo_oauth_flow()
        await demo_chat_integration()
        await demo_ai_processing()
        await demo_ticket_operations()
        await demo_complete_pipeline()
        await demo_provider_switching()
        await demo_observability()

        print_section("Demo Complete!")

    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Demo error occurred")


if __name__ == "__main__":
    asyncio.run(main())
