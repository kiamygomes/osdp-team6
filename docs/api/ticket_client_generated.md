# Ticket Client Generated

Auto-generated HTTP client from the Ticket Service OpenAPI specification.

## Features

- Type-safe async HTTP client
- Generated Pydantic models for requests/responses
- Built on `httpx` for high performance
- Structured error handling

## Components

::: ticket_service_client.Client

::: ticket_service_client.AuthenticatedClient

## Usage

```python
from ticket_service_client import Client
from ticket_service_client.api.tickets import create_ticket_api_v1_tickets_post
from ticket_service_client.models import TicketCreateRequest, TicketPriority

# Initialize client
client = Client(base_url="http://localhost:8000")

# Create request
request = TicketCreateRequest(
    title="Bug Report",
    description="Issue description",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)

# Make API call
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client,
    body=request,
    x_user_id="user-id",
    x_project_key="PROJ"
)
```

## Generation

Generated using `openapi-python-client`:

```bash
openapi-python-client generate \
    --url http://localhost:8000/api/v1/openapi.json \
    --output-path src/ticket_client_generated
```