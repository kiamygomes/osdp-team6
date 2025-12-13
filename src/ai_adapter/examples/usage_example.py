# /Users/Mikiyas/Desktop/Open_Source/osdp-team6/src/ai_adapter/examples/usage_example.py
"""Example usage of the AI Adapter with the ticketing system.

This example demonstrates how to integrate the Claude service with
the ticketing system to process natural language commands.
"""

import asyncio

from fast_api_client import Client as ClaudeClient
from ticket_impl import TicketImpl

from ai_adapter import AITicketAdapter


async def main():
    """Demonstrate AI adapter usage."""
    # Initialize the Claude service client
    # In production, this would connect to your deployed AI service
    claude_client = ClaudeClient(base_url="http://localhost:8001")

    # Initialize the ticket service
    # This could be a local TicketImpl or a RemoteTicketService
    ticket_service = TicketImpl(
        user_id="demo-user@example.com",
        project_key="DEMO",
    )

    # Create the AI adapter
    adapter = AITicketAdapter(
        ticket_service=ticket_service,
        claude_client=claude_client,
        user_id="demo-user@example.com",
        project_key="DEMO",
    )

    # Example 1: Create a ticket with natural language
    print("Example 1: Creating a ticket")
    result = await adapter.process_command(
        "Create a ticket for fixing the login bug with high priority"
    )
    print(f"Result: {result.message}")
    if result.success and result.data:
        print(f"Created ticket ID: {result.data.id}")
    print()

    # Example 2: List tickets
    print("Example 2: Listing tickets")
    result = await adapter.process_command(
        "Show me all open tickets"
    )
    print(f"Result: {result.message}")
    if result.success and result.data:
        for ticket in result.data:
            print(f"  - {ticket.title} ({ticket.status.value})")
    print()

    # Example 3: Update a ticket status
    print("Example 3: Updating ticket status")
    result = await adapter.process_command(
        "Mark the login bug ticket as in progress"
    )
    print(f"Result: {result.message}")
    print()

    # Example 4: Add a comment
    print("Example 4: Adding a comment")
    result = await adapter.process_command(
        "Add a comment to the ticket saying 'Working on this now'"
    )
    print(f"Result: {result.message}")
    print()

    # Example 5: Ambiguous request (Claude will ask for clarification)
    print("Example 5: Ambiguous request")
    result = await adapter.process_command(
        "Update the ticket"
    )
    print(f"Result: {result.message}")


if __name__ == "__main__":
    asyncio.run(main())
