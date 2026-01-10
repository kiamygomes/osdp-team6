# Ticket Service Client

Auto-generated HTTP client for the Ticket Service API.

## Purpose

- Generated from OpenAPI 3.0 specification
- Type-safe HTTP methods for all endpoints
- Pydantic models for requests/responses
- Async and sync support

## Installation

```bash
uv add ticket-service-client
```

## Usage

```python
from ticket_service_client import Client
from ticket_service_client.api.tickets import create_ticket_api_v1_tickets_post
from ticket_service_client.models import TicketCreateRequest, TicketPriority

client = Client(base_url="http://localhost:8000")

request = TicketCreateRequest(
    title="Bug Report",
    description="System issue",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)

response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client,
    body=request,
    x_user_id="user-id",
    x_project_key="PROJ"
)

if response.status_code == 201:
    ticket = response.parsed
    print(f"Created: {ticket.id}")
```

## API Modules

- `ticket_service_client.api.tickets` - Ticket operations
- `ticket_service_client.api.comments` - Comment operations
- `ticket_service_client.models` - Request/response models

## Generation

Generated using `openapi-python-client`:

```bash
# From running service
openapi-python-client generate \
    --url http://localhost:8000/api/v1/openapi.json \
    --output-path src/ticket_client_generated
```

## Note

**Don't use this directly!** Use `ticket_client_adapter` instead, which wraps this client with:
- Clean `TicketServiceAPI` interface
- Retry logic and circuit breaker
- Idempotency support
- Domain model conversion

```python
# Better: Use the adapter
from ticket_client_adapter import RemoteTicketService
service = RemoteTicketService(base_url="http://localhost:8000", ...)
ticket = await service.create_ticket(...)
```

## Testing

```bash
uv run pytest src/ticket_client_generated/tests/ -v
```
