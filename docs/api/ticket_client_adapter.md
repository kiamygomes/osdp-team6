# Ticket Client Adapter

HTTP client with enterprise reliability features.

## Overview

- **Package**: `ticket_client_adapter`
- **Purpose**: Remote `TicketServiceAPI` implementation
- **Dependencies**: httpx, ticket-service-client
- **Coverage**: 95%+ (50+ tests)

## Key Features

- Implements `TicketServiceAPI` for HTTP access
- Retry logic with exponential backoff
- Circuit breaker pattern
- Idempotency support
- Correlation IDs for tracing

## Usage

```python
from ticket_client_adapter import RemoteTicketService

async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ",
    max_retries=3
) as service:
    ticket = await service.create_ticket(
        title="Bug Report",
        description="System issue",
        reporter="user@example.com"
    )
```

## Reliability Features

**Retry Logic:**
- Retries 5xx and 429 errors
- Exponential backoff with jitter
- Respects `Retry-After` header
- Configurable max retries

**Circuit Breaker:**
- Opens after 5 failures
- Prevents cascading failures
- Recovers after 60 seconds

**Idempotency:**
- Generates keys for create/update/delete
- Safe to retry without duplicates
- Hash-based deterministic keys

**Observability:**
- Correlation IDs for tracing
- Structured logging
- Request/response timing

## Configuration

```python
service = RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ",
    max_retries=3,
    initial_backoff_seconds=1.0,
    timeout=30.0
)
```

## Error Handling

- 4xx (except 429): Fail immediately
- 5xx: Retry with backoff
- 429: Retry with backoff
- Network errors: Retry
- Circuit open: Fail fast

## Related

- [ticket_api](ticket_api.md) - Abstract interface
- [ticket_service](ticket_service.md) - REST API this connects to
