# Chat API

Abstract interface for chat platform integration. This package defines the contract for how the orchestrator communicates with chat services (like Slack, Discord, etc.).

## Purpose

The Chat API provides an abstract base class (`ChatClientProtocol`) that defines the interface for:
- Receiving messages from chat platforms
- Processing commands through the orchestrator
- Sending responses back to chat channels

This abstraction allows the system to work with any chat platform that implements the interface.

## Core Interface

### `ChatClientProtocol`

```python
class ChatClientProtocol(Protocol):
    """Protocol for chat client implementations."""
    
    async def handle_message(
        self, 
        channel_id: str, 
        user_id: str, 
        message: str
    ) -> str:
        """Handle an incoming chat message and return response."""
        ...
    
    async def send_message(
        self, 
        channel_id: str, 
        message: str
    ) -> None:
        """Send a message to a chat channel."""
        ...
```

## Usage

### With the Orchestrator

```python
from orchestrator.main_app import TicketBotOrchestrator

orchestrator = TicketBotOrchestrator(
    user_id="user-123",
    project_key="PROJ",
    ai_provider="claude"
)

# Process chat message
result = await orchestrator.process_chat_message(
    message="Create a ticket for the login bug",
    channel_id="general"
)

# Send response back to chat
if result.get("success"):
    await chat_client.send_message(
        channel_id="general",
        message=result.get("message", "Operation completed")
    )
```

### Implementing a Chat Client

To create a new chat platform integration:

```python
from chat_api import ChatClientProtocol

class SlackClient:
    """Slack implementation of ChatClientProtocol."""
    
    async def handle_message(
        self, 
        channel_id: str, 
        user_id: str, 
        message: str
    ) -> str:
        # Process message and return response
        return f"Processed: {message}"
    
    async def send_message(
        self, 
        channel_id: str, 
        message: str
    ) -> None:
        # Send message to Slack channel
        await self.slack_client.chat_postMessage(
            channel=channel_id,
            text=message
        )
```

## Integration Points

The chat API integrates with:

1. **Orchestrator** (`src/orchestrator`): Routes messages through the ticket pipeline
2. **External Chat Teams** (`external/slack_team`, `external/discord_team`): Chat platform implementations
3. **Ticket Service** (`src/ticket_service`): Executes ticket operations

## Data Models

### Chat Message Context
- `channel_id`: Identifier for the chat channel
- `user_id`: Identifier for the user sending the message
- `message`: Natural language command/message text
- `timestamp`: When the message was received

### Response Format
- `success`: Boolean indicating if operation succeeded
- `message`: Human-readable response message
- `data`: Structured result data (if applicable)

## Flow Diagram

```
User Types Message
       ↓
Chat Platform (Slack/Discord)
       ↓
ChatClient.handle_message()
       ↓
Orchestrator.process_chat_message()
       ↓
AI Service → Ticket Service
       ↓
ChatClient.send_message()
       ↓
Response in Chat Channel
```

## Testing

Test your chat client implementation:

```python
import pytest
from chat_api import ChatClientProtocol

@pytest.mark.asyncio
async def test_chat_client_handles_message():
    client = MyCustomChatClient()
    result = await client.handle_message(
        channel_id="general",
        user_id="user-123",
        message="Create a ticket"
    )
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_chat_client_sends_message():
    client = MyCustomChatClient()
    await client.send_message(
        channel_id="general",
        message="Ticket created!"
    )
    # Verify message was sent
```

## Configuration

Chat client implementations should support configuration via environment variables:

```bash
# Example for Slack
SLACK_BOT_TOKEN="xoxb-your-token"
SLACK_SIGNING_SECRET="your-secret"

# Example for Discord
DISCORD_TOKEN="your-discord-token"
```

## Further Reading

- [Orchestrator Documentation](../orchestrator/README.md)
- [Architecture Design](../../DESIGN.md)
- [Integration Guide](../../docs/component.md)
