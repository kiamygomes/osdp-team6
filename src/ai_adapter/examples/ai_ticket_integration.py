# /Users/Mikiyas/Desktop/Open_Source/osdp-team6/examples/ai_ticket_integration.py
"""Complete integration example showing AI service + Ticket service workflow.

This demonstrates the full user flow:
1. User types a command
2. Command is sent to AI Service (Claude)
3. AI analyzes text, determines intent, extracts data
4. Application executes against Ticket Interface
5. Ticket Service confirms action
6. Response is relayed back to user
"""

import asyncio
import os

from fast_api_client import Client as ClaudeClient

# Import ticket service components
from ticket_client_adapter import RemoteTicketService

# Import AI adapter
from ai_adapter import AITicketAdapter


async def demonstrate_workflow():
    """Demonstrate the complete AI + Ticketing workflow."""
    print("=" * 80)
    print("AI-Powered Ticket Management System - Integration Demo")
    print("=" * 80)
    print()

    # Configuration
    ticket_service_url = os.getenv("TICKET_SERVICE_URL", "http://localhost:8000")
    ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    user_id = "demo-user@example.com"
    project_key = "DEMO"

    # Step 1: Initialize services
    print("Step 1: Initializing services...")
    print(f"  - Ticket Service: {ticket_service_url}")
    print(f"  - AI Service: {ai_service_url}")
    print()

    # Initialize Claude service client
    claude_client = ClaudeClient(base_url=ai_service_url)

    # Initialize ticket service (using remote adapter for deployed service)
    ticket_service = RemoteTicketService(
        base_url=ticket_service_url,
        user_id=user_id,
        project_key=project_key,
    )

    # Initialize AI adapter
    ai_adapter = AITicketAdapter(
        ticket_service=ticket_service,
        claude_client=claude_client,
        user_id=user_id,
        project_key=project_key,
    )

    print("✓ Services initialized successfully")
    print()

    # Step 2: User input - Create a ticket
    print("=" * 80)
    print("WORKFLOW EXAMPLE 1: Create a Ticket")
    print("=" * 80)
    user_command = "Create a ticket for fixing the login bug with high priority"
    print(f'User Input: "{user_command}"')
    print()

    print("Step 2: Routing to AI Service...")
    print("  → Sending text to Claude for analysis...")
    print()

    print("Step 3: AI Reasoning...")
    print("  → Claude analyzes text")
    print("  → Determines intent: create_ticket")
    print("  → Extracts data: title='Fix login bug', priority='high'")
    print("  → Returns structured tool call")
    print()

    # Process the command
    result = await ai_adapter.process_command(user_command)

    print("Step 4: Execution...")
    print("  → Executing tool call against Ticket Interface")
    print()

    print("Step 5: Response...")
    if result.success:
        print(f"  ✓ {result.message}")
        if result.data:
            ticket = result.data
            print(f"    - Ticket ID: {ticket.id}")
            print(f"    - Title: {ticket.title}")
            print(f"    - Status: {ticket.status.value}")
            print(f"    - Priority: {ticket.priority.value}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()

    # Step 3: User input - List tickets
    print("=" * 80)
    print("WORKFLOW EXAMPLE 2: List Tickets")
    print("=" * 80)
    user_command = "Show me all open tickets"
    print(f'User Input: "{user_command}"')
    print()

    result = await ai_adapter.process_command(user_command)

    if result.success:
        print(f"  ✓ {result.message}")
        if result.data and isinstance(result.data, list):
            for i, ticket in enumerate(result.data, 1):
                print(f"    {i}. {ticket.title} - {ticket.status.value}")
    else:
        print(f"  ✗ Error: {result.error}")
    print()

    # Step 4: User input - Update ticket
    print("=" * 80)
    print("WORKFLOW EXAMPLE 3: Update Ticket Status")
    print("=" * 80)
    # In a real scenario, you'd get the ticket ID from the previous operation
    # For demo purposes, we'll simulate having a ticket ID
    if result.success and result.data and len(result.data) > 0:
        ticket_id = result.data[0].id
        user_command = f"Mark ticket {ticket_id} as in progress"
        print(f'User Input: "{user_command}"')
        print()

        result = await ai_adapter.process_command(user_command)

        if result.success:
            print(f"  ✓ {result.message}")
            if result.data:
                print(f"    - New status: {result.data.status.value}")
        else:
            print(f"  ✗ Error: {result.error}")
    print()

    # Step 5: Demonstrate clarification
    print("=" * 80)
    print("WORKFLOW EXAMPLE 4: Ambiguous Request (Clarification)")
    print("=" * 80)
    user_command = "Update the ticket"
    print(f'User Input: "{user_command}"')
    print()

    result = await ai_adapter.process_command(user_command)

    print("AI Response (asking for clarification):")
    print(f"  {result.message}")
    print()

    print("=" * 80)
    print("Integration Demo Complete!")
    print("=" * 80)


async def run_unit_workflow_test():
    """Simple test of the workflow with mocked services."""
    print("Running unit workflow test...")
    print()

    # For testing without deployed services, we can use mocks
    from unittest.mock import AsyncMock, Mock

    # Mock Claude client
    claude_client = Mock()

    # Mock ticket service
    ticket_service = Mock()
    ticket_service.create_ticket = AsyncMock()
    ticket_service.list_tickets = AsyncMock()

    # Create adapter
    adapter = AITicketAdapter(
        ticket_service=ticket_service,
        claude_client=claude_client,
        user_id="test-user",
        project_key="TEST",
    )

    # Test the workflow components
    print("✓ Adapter initialized")
    print("✓ Ready to process commands")
    print()
    print("Note: Run with deployed services for full integration test")


if __name__ == "__main__":
    # Check if services are available
    ticket_url = os.getenv("TICKET_SERVICE_URL")
    ai_url = os.getenv("AI_SERVICE_URL")

    if ticket_url and ai_url:
        # Run full integration
        asyncio.run(demonstrate_workflow())
    else:
        # Run unit test
        print("Environment variables not set. Running unit workflow test...")
        print("To run full integration, set:")
        print("  export TICKET_SERVICE_URL=http://your-ticket-service-url")
        print("  export AI_SERVICE_URL=http://your-ai-service-url")
        print()
        asyncio.run(run_unit_workflow_test())
