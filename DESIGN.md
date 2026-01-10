# Design Document — AI-Powered Ticket Management System

This document describes the architecture and design of the multi-team integration system. It covers the main orchestrator, AI integration layer, FastAPI service, auto-generated API client, and the adapters that enable seamless communication between Chat, AI, and Ticketing services.

## Architecture Overview

The system implements a **multi-team integration architecture** with the following key components:

- **`orchestrator`** (Main Application): Coordinates the complete Chat → AI → Tickets pipeline using the `TicketBotOrchestrator` class.
- **AI Integration Layer**: Connects with external AI teams (Claude and OpenAI) to process natural language commands into structured ticket operations.
- **`ticket_service`** (FastAPI service): Wraps the existing `ticket_impl` library and exposes it over HTTP for distributed access.
- **`ticket_client_generated`** (auto-generated client): OpenAPI/HTTP client that communicates with the FastAPI service.
- **`ticket_client_adapter`** (adapter/shim): Implements `TicketServiceAPI` by delegating to the generated client for location transparency.
- **`ticket_impl` / `ticket_api`** (core library): The original in-process Jira client and ticket models.
- **External Team Packages**: Git submodules containing Claude team, OpenAI team, and Slack team implementations.

**Key idea**: The orchestrator processes natural language commands through AI services to generate structured ticket operations, while maintaining the same `TicketServiceAPI` interface regardless of whether the implementation is local or remote.

## Components Added

- **orchestrator** (`src/orchestrator/src/orchestrator/main_app.py`)
  - `TicketBotOrchestrator` class that coordinates the complete Chat → AI → Tickets pipeline
  - Supports AI provider switching between Claude and OpenAI teams
  - Implements `process_chat_message()` for natural language command processing
  - Provides chat integration through `ChatClientProtocol`
  - Handles bidirectional communication: `process_incoming_chat()` and `send_to_chat()`

- **AI Integration Layer** (`src/ai_adapter/`, `src/ai_implementations/`)
  - `ClaudeTeamAdapter` and `OpenAITeamAdapter` for connecting with external AI teams
  - Natural language processing to structured tool calls
  - Error handling and fallback mechanisms for AI service failures
  - Integration with external team packages via git submodules

- **ticket_service** (`src/ticket_service/src/ticket_service/main.py`)
  - FastAPI app exposing endpoints:
    - `GET /api/v1/auth/login` — OAuth flow
    - `GET /api/v1/auth/callback` — OAuth callback, sets cookie
    - `GET /api/v1/auth/status` — check authentication
    - `POST /api/v1/auth/logout` — clear session
    - `POST /api/v1/tickets` — create ticket
    - `GET /api/v1/tickets/{id}` — get ticket
    - `GET /api/v1/tickets` — list tickets
    - `PATCH /api/v1/tickets/{id}` — update ticket
    - `DELETE /api/v1/tickets/{id}` — delete ticket
    - `POST /api/v1/tickets/{id}/comments` — add comment
    - `GET /api/v1/tickets/{id}/comments` — get comments
    - `GET /health` — health check
  - The service uses dependency injection to instantiate `TicketImpl` with user context from cookies/headers.
  - Error mapping: service maps underlying exceptions to HTTP status codes (400/401/404/500).

- **ticket_client_generated** (`src/ticket_client_generated/...`)
  - Auto-generated client using httpx.
  - Provides async functions for each endpoint, returning deserialized JSON or raising on unexpected status codes.

- **ticket_client_adapter** (`src/ticket_client_adapter/src/ticket_client_adapter/client.py`)
  - `RemoteTicketService` implements `TicketServiceAPI` by delegating to the generated client.
  - Adds retry logic, circuit breaker, and idempotency support.
  - Converts between domain models (dataclasses) and generated models (Pydantic).

- **External Team Integration** (`external/*/`)
  - Git submodules containing Claude team, OpenAI team, and Slack team packages
  - Each team provides their own API interfaces and implementations
  - Integrated through adapter pattern to maintain clean boundaries

## Example Request Flow

**Scenario:** User types "Create a high priority ticket for fixing the login bug" in chat

### Complete Pipeline: Chat → AI → Tickets → Response

1. **User Input Processing**
   ```python
   orchestrator = TicketBotOrchestrator(
       user_id="user-123", 
       project_key="PROJ", 
       ai_provider="claude"
   )
   
   result = await orchestrator.process_chat_message(
       "Create a high priority ticket for fixing the login bug"
   )
   ```

2. **AI Processing**
   - `ClaudeTeamAdapter.process_command()` sends natural language to Claude AI service
   - Claude AI analyzes text and returns structured tool call:
   ```json
   {
     "tool": "create_ticket",
     "parameters": {
       "title": "Fix login bug",
       "description": "Users cannot authenticate - login functionality broken",
       "priority": "high",
       "reporter": "user-123"
     }
   }
   ```

3. **Ticket Operation Execution**
   - AI adapter calls `TicketImpl.create_ticket()` with structured parameters
   - `TicketImpl` performs OAuth authentication with Jira
   - Creates ticket in Jira Cloud via REST API
   - Stores UUID mapping in local database
   - Returns domain `Ticket` object

4. **Response Generation**
   - AI adapter formats success response:
   ```python
   {
     "success": True,
     "message": "Successfully created ticket: Fix login bug (ID: 550e8400-e29b-41d4-a716-446655440000)",
     "data": ticket_object,
     "error": None
   }
   ```

5. **Chat Integration (Optional)**
   - If chat client available, sends response back to chat channel
   - Otherwise logs the response for CLI/demo purposes

### Alternative Flow: HTTP Service Access

For distributed deployments, the same ticket operations can be accessed via HTTP:

1. **HTTP Client Call**
   ```python
   remote_service = RemoteTicketService(
       base_url="http://localhost:8000",
       user_id="user-123", 
       project_key="PROJ"
   )
   ticket = await remote_service.create_ticket(...)
   ```

2. **HTTP Request**
   ```
   POST http://localhost:8000/api/v1/tickets
   Headers: X-User-ID, X-Project-Key, Idempotency-Key
   Body: {"title": "Fix login bug", "description": "...", "priority": "high"}
   ```

3. **FastAPI Processing**
   - Same `TicketImpl` logic as direct integration
   - Returns JSON response that gets converted back to domain objects

## Sample API Response

`POST /api/v1/tickets` → 201 Created:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Bug in login",
  "description": "Users cannot authenticate",
  "status": "open",
  "priority": "high",
  "assignee": null,
  "reporter": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "comments": []
}
```

`GET /api/v1/tickets` → 200 OK:
```json
{
  "tickets": [...],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

Error (404 Not Found):
```json
{
  "detail": "Ticket 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

## API Design

**Endpoints:**

- `GET /api/v1/auth/login`
  - Response: 302 Redirect to Jira OAuth
- `GET /api/v1/auth/callback?code={code}&state={state}`
  - Success: 200 with cookie set
  - Errors: 400 (invalid state)
- `POST /api/v1/tickets`
  - Success: 201 Created
  - Errors: 400 (validation), 401 (not authenticated), 500 (server error)
- `GET /api/v1/tickets/{id}`
  - Success: 200 OK
  - Errors: 401, 404, 500
- `GET /api/v1/tickets?status={status}&limit={limit}&offset={offset}`
  - Success: 200 OK
  - Errors: 401, 500
- `PATCH /api/v1/tickets/{id}`
  - Success: 200 OK
  - Errors: 400, 401, 404, 500
- `DELETE /api/v1/tickets/{id}`
  - Success: 204 No Content
  - Errors: 401, 404, 500
- `POST /api/v1/tickets/{id}/comments`
  - Success: 201 Created
  - Errors: 400, 401, 404, 500

**Error handling strategy:**

The service maps underlying exceptions to HTTP status codes:
- `ValueError` → 400 Bad Request
- `TicketNotFoundError` → 404 Not Found
- `ServiceError` → 500 Internal Server Error
- Missing authentication → 401 Unauthorized

The adapter retries 5xx and 429 errors with exponential backoff. 4xx errors (except 429) fail immediately.

## Adapter Pattern

The auto-generated client returns JSON payloads shaped after the OpenAPI spec. The `TicketServiceAPI` interface expects methods that return domain `Ticket` dataclasses. Without an adapter, the generated client would require consumers to:
- Call HTTP methods directly with explicit `Client` objects
- Parse JSON into domain models
- Handle HTTP errors and map them back to domain exceptions
- Manage headers and authentication

This breaks the promise that user code should be identical whether using the library or the service.

**How the adapter works (code snippet)**

User code calling the adapter looks identical to calling the original library:

```python
from ticket_client_adapter import RemoteTicketService

# Service
async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ"
) as service:
    ticket = await service.create_ticket(
        title="Bug Report",
        description="System issue",
        reporter="user@example.com"
    )

# Library (for comparison)
from ticket_impl import TicketImpl
service = TicketImpl(user_id="user-123", project_key="PROJ")
ticket = await service.create_ticket(...)
```

**Adapter internals:**
- Composes an `IdempotentClient` (extends generated `Client`) with retry/circuit breaker logic
- Each adapter method calls the corresponding generated function and converts models
- Generates idempotency keys for safe retries on create/update/delete operations
- Adds correlation IDs for request tracing

## Testing Strategy

**What was tested**
- Unit tests for `ticket_service` FastAPI app using `TestClient` with mocked `TicketImpl`
- Adapter tests mock generated client functions to avoid real HTTP requests
- Contract tests validate `TicketServiceAPI` implementations
- Integration tests exercise full stack with mocked Jira API

**Test types**
- Unit: Isolated component tests with mocked dependencies (140+ tests total)
- Integration: Component interaction tests (15+ tests)
- E2E: Full stack tests with real service, mocked Jira only

**Mocking strategy**
- `ticket_service` tests mock `TicketImpl` to avoid Jira API calls
- `ticket_client_adapter` tests mock generated client functions to prevent HTTP requests
- `ticket_impl` tests mock `httpx.AsyncClient` to avoid real Jira API calls
- OAuth token exchange always mocked in tests

**Interface compliance**
- MyPy static type checking ensures `RemoteTicketService` implements all `TicketServiceAPI` methods
- Python ABC enforcement prevents instantiation if methods are missing
- Contract tests in `src/ticket_api/tests/` validate expected behavior
- Integration tests use adapter as `TicketServiceAPI` type to verify runtime compliance
