# Ticket Client Adapter

HTTP client adapter implementing `TicketServiceAPI` with enterprise reliability features.

## Purpose

- Implements `TicketServiceAPI` for remote HTTP access
- Wraps auto-generated client with clean interface
- Adds retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Idempotency support for safe retries
- Correlation IDs for request tracing

## Installation

```bash
uv add ticket-client-adapter
```

## Usage

```python
from ticket_client_adapter import RemoteTicketService

async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ",
    max_retries=3
) as service:
    # Same interface as TicketImpl!
    ticket = await service.create_ticket(
        title="Bug Report",
        description="System issue",
        reporter="user@example.com"
    )
```

## Reliability Features

### Retry Logic
- Retries 5xx and 429 errors
- Exponential backoff with jitter
- Respects `Retry-After` header
- Configurable max retries (default: 3)

### Circuit Breaker
- Opens after 5 consecutive failures
- Prevents cascading failures
- Recovers after 60 seconds
- Fails fast when open

### Idempotency
- Generates idempotency keys for create/update/delete
- Safe to retry without duplicates
- Hash-based deterministic keys

### Observability
- Correlation IDs for request tracing
- Structured logging with context
- Request/response timing

## Configuration

```python
service = RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ",
    max_retries=3,                    # Retry attempts
    initial_backoff_seconds=1.0,      # Initial backoff
    timeout=30.0                      # Request timeout
)
```

## Error Handling

- 4xx errors (except 429): Fail immediately
- 5xx errors: Retry with backoff
- 429 (rate limit): Retry with backoff
- Network errors: Retry with backoff
- Circuit breaker open: Fail immediately

## Testing

```bash
uv run pytest src/ticket_client_adapter/tests/ -v
```

**Coverage:** 95%+ (50+ tests)

Tests mock HTTP responses - no real service calls.

## Why Use This?

**Without adapter:**
- Manual HTTP client management
- Parse JSON responses
- Handle status codes
- Implement retries yourself
- No circuit breaker
- No idempotency

**With adapter:**
- Clean `TicketServiceAPI` interface
- Automatic model conversion
- Built-in reliability features
- Production-ready
- Same code as library usage
