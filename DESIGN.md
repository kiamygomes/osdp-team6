# Design Document — Ticket Service

This document describes the architecture and design of the service-based implementation. It covers the FastAPI service, the auto-generated API client, and the adapter that allows user code to consume the service with the same interface as the original library.

## Architecture Overview

- `ticket_service` (FastAPI service): wraps the existing `ticket_impl` library and exposes it over HTTP.
- `ticket_client_generated` (auto-generated client): OpenAPI/HTTP client that communicates with the FastAPI service.
- `ticket_client_adapter` (adapter/shim): implements `TicketServiceAPI` by delegating to the generated client so user code does not have to change.
- `ticket_impl` / `ticket_api` (existing library code): the original in-process Jira client and ticket models.

**Key idea**: user code calls the same methods (`create_ticket`, `get_ticket`, `list_tickets`, etc.) regardless of whether the implementation is local or remote.

## Components Added

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

## Example Request Flow

**Scenario:** user code calls `service.create_ticket(title="Bug", description="...", reporter="...")`

1. **User code obtains a client**
   - `RemoteTicketService(base_url="http://localhost:8000", user_id="user-123", project_key="PROJ")`

2. **Adapter call**
   - `RemoteTicketService.create_ticket()` generates idempotency key, converts to `TicketCreateRequest`, calls:
   ```python
   create_ticket_api_v1_tickets_post.asyncio_detailed(
       client=self._client,
       body=request,
       x_user_id=self._user_id,
       x_project_key=self._project_key
   )
   ```

3. **HTTP request**
   - `httpx` sends:
   ```
   POST http://localhost:8000/api/v1/tickets
   Headers: X-User-ID, X-Project-Key, Idempotency-Key
   Body: {"title": "Bug", "description": "...", "reporter": "...", "priority": "medium"}
   ```

4. **FastAPI endpoint `/api/v1/tickets` executes:**
   - Validates request with Pydantic
   - Calls dependency-injected `TicketImpl`:
   ```python
   ticket = await service.create_ticket(
       title=request.title,
       description=request.description,
       reporter=request.reporter,
       priority=request.priority
   )
   ```
   - `TicketImpl` calls Jira API, stores UUID mapping, returns domain `Ticket`
   - Serializes `Ticket` to JSON:
   ```json
   {
     "id": "550e8400-e29b-41d4-a716-446655440000",
     "title": "Bug",
     "status": "open",
     "priority": "medium",
     "reporter": "user@example.com",
     "created_at": "2024-01-15T10:30:00Z"
   }
   ```

5. **Response handling**
   - Generated client returns parsed `TicketResponse` to adapter.

6. **Adapter conversion**
   - `RemoteTicketService` converts `TicketResponse` back to domain `Ticket` dataclass.
   - Returns to user code.

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
