# Orchestrator

Main FastAPI application that coordinates the complete **Chat → AI → Tickets** pipeline. The orchestrator processes natural language commands from chat, routes them through AI services (Claude or OpenAI), and executes corresponding ticket operations.

## Overview

The orchestrator implements a multi-team integration architecture that brings together:
- **Chat Interface**: Receives natural language commands from users
- **AI Processing**: Processes commands through Claude or OpenAI teams
- **Ticket Management**: Executes structured ticket operations (create, update, delete, etc.)

## Key Components

### `TicketBotOrchestrator` Class
The main orchestrator class that coordinates the entire pipeline:

```python
orchestrator = TicketBotOrchestrator(
    user_id="user-123",
    project_key="PROJ",
    ai_provider="claude"  # or "openai"
)

# Process natural language command
result = await orchestrator.process_chat_message("Create a ticket for the login bug")
```

### Core Methods

- **`process_chat_message(message, channel_id=None)`**
  - Main entry point for processing natural language commands
  - Routes through AI service for interpretation
  - Executes resulting ticket operations
  - Returns structured response with results

- **`process_incoming_chat(message, channel_id, user_id)`**
  - Handles incoming chat messages from integrated chat platforms
  - Maintains chat context and user information
  - Processes and returns responses

- **`send_to_chat(channel_id, message)`**
  - Sends responses back to chat platform
  - Maintains bidirectional communication

## API Endpoints

### Process Command
```http
POST /process
Content-Type: application/json

{
  "message": "Create a high priority ticket for fixing the login bug",
  "user_id": "demo_user",
  "project_key": "DEMO",
  "ai_provider": "claude"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Created ticket DEMO-123",
  "data": {
    "id": "...",
    "title": "Fix login bug",
    "priority": "high",
    "status": "open"
  }
}
```

### Process Chat Message
```http
POST /process-chat
Content-Type: application/json

{
  "message": "Create a ticket for the login bug",
  "channel_id": "general",
  "user_id": "demo_user",
  "project_key": "DEMO",
  "ai_provider": "claude"
}
```

### Health Check
```http
GET /health
```

Returns service health status.

### Status
```http
GET /status
```

Returns service status and configuration information.

## Configuration

Set environment variables to configure the orchestrator:

- `JIRA_CLOUD_ID`: Jira Cloud instance ID
- `JIRA_CLIENT_ID`: OAuth client ID for Jira
- `JIRA_CLIENT_SECRET`: OAuth client secret for Jira
- `JIRA_REDIRECT_URI`: OAuth redirect URI
- `AI_PROVIDER`: Default AI provider (`claude` or `openai`)

## Running the Orchestrator

### Development
```bash
cd src/orchestrator
uv run uvicorn src.orchestrator.orchestrator_service:app --reload
```

### Production
```bash
uv run gunicorn "src.orchestrator.orchestrator_service:app" --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Testing

Run tests for the orchestrator:

```bash
# All tests
uv run pytest tests/test_main_app.py -v

# Specific test class
uv run pytest tests/test_main_app.py::TestOrchestrator -v

# With coverage
uv run pytest tests/test_main_app.py --cov=src/orchestrator
```

## Architecture

The orchestrator uses a layered architecture:

```
┌─────────────────────────────────────┐
│  FastAPI Web Service                │
│  (REST Endpoints)                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  TicketBotOrchestrator              │
│  (Main Orchestration Logic)         │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐ ┌─────▼──────────┐
│ AI Adapter  │ │ Ticket Service │
│ (Claude/OAI)│ │ (Jira/Remote)  │
└─────────────┘ └────────────────┘
```

## Error Handling

The orchestrator handles errors gracefully:

- **AI Service Errors**: Falls back to alternative AI provider if configured
- **Ticket Service Errors**: Returns structured error response
- **Validation Errors**: Returns 400 Bad Request with details
- **Authentication Errors**: Returns 401 Unauthorized
- **Server Errors**: Returns 500 Internal Server Error with details

## Integration with External Teams

The orchestrator integrates with:

- **Claude AI Team** (`external/claude_team`): Natural language processing
- **OpenAI Team** (`external/openai_team`): Alternative AI provider
- **Slack Team** (`external/slack_team`): Chat platform integration

## Monitoring and Observability

The orchestrator includes:

- **Prometheus Metrics**: Request latency, success/failure rates
- **Structured Logging**: JSON logs for debugging and monitoring
- **Health Checks**: Built-in health check endpoint

Access metrics at: `GET /metrics`

## Dependencies

Core dependencies (from `pyproject.toml`):
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `httpx`: Async HTTP client
- `prometheus-client`: Metrics collection

## Further Reading

- [Architecture Design](../../DESIGN.md)
- [AI Adapter Documentation](../ai_adapter/README.md)
- [Ticket Service Documentation](../ticket_service/README.md)
- [API Documentation](../../docs/api/README.md)
