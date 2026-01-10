# Ticket Client Generated

Auto-generated HTTP client from OpenAPI spec.

## Overview

- **Package**: `ticket_client_generated`
- **Purpose**: Type-safe HTTP client
- **Generated**: From OpenAPI 3.0 spec
- **Note**: Use `ticket_client_adapter` instead

## Features

- Auto-generated from service OpenAPI spec
- Type-safe Pydantic models
- Async and sync support
- Comprehensive error handling

## Generation

```bash
openapi-python-client generate \
    --url http://localhost:8000/api/v1/openapi.json \
    --output-path src/ticket_client_generated
```

## Usage

```python
from ticket_service_client import Client
from ticket_service_client.api.tickets import create_ticket_api_v1_tickets_post

client = Client(base_url="http://localhost:8000")
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client,
    body=request,
    x_user_id="user-id",
    x_project_key="PROJ"
)
```

## Recommendation

**Don't use this directly!** Use `ticket_client_adapter` instead for:
- Clean `TicketServiceAPI` interface
- Retry logic and circuit breaker
- Idempotency support
- Domain model conversion

## Related

- [ticket_client_adapter](ticket_client_adapter.md) - Recommended wrapper
- [ticket_service](ticket_service.md) - Service this client connects to
