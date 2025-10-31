# Ticket Service Client

Auto-generated HTTP client for the Ticket Service API, providing type-safe access to all service endpoints.

## Overview

This package contains auto-generated client code created from the Ticket Service OpenAPI specification. It provides:

- Type-safe HTTP client methods for all endpoints
- Generated Pydantic models for requests and responses
- Async and sync operation support
- Comprehensive error handling
- Full OpenAPI 3.0 compatibility

## Usage

### Basic Client Setup

```python
from ticket_service_client import Client

client = Client(base_url="http://localhost:8000")
```

### Making API Calls

```python
from ticket_service_client.api.tickets import create_ticket_api_v1_tickets_post
from ticket_service_client.models import TicketCreateRequest, TicketPriority

# Create request model
request = TicketCreateRequest(
    title="Bug Report",
    description="System issue description",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)

# Make async API call
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client,
    body=request,
    x_user_id="user-id",
    x_project_key="PROJ"
)

# Handle response
if response.status_code == 201:
    ticket = response.parsed
    print(f"Created ticket: {ticket.id}")
```

### API Organization

The generated client organizes endpoints into modules:

- `ticket_service_client.api.tickets` - Ticket CRUD operations
- `ticket_service_client.api.comments` - Comment operations
- `ticket_service_client.models` - Request/response models

### Response Handling

Each endpoint provides multiple response access patterns:

```python
# Get parsed response data only
ticket = await create_ticket_api_v1_tickets_post.asyncio(
    client=client, body=request, x_user_id="user-id", x_project_key="PROJ"
)

# Get detailed response with status code and headers
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client, body=request, x_user_id="user-id", x_project_key="PROJ"
)
print(f"Status: {response.status_code}")
print(f"Data: {response.parsed}")
```

## Testing

The generated client includes basic functionality tests:

### Test Structure

**test_generated_client.py** - Generated client functionality
- Client initialization and configuration
- Basic endpoint accessibility
- Model import and usage
- Error handling scenarios

### Running Tests

```bash
# All generated client tests
uv run pytest src/ticket_client_generated/tests/ -v

# Coverage reporting
uv run pytest src/ticket_client_generated/tests/ --cov=ticket_service_client --cov-report=term-missing
```

## Generation

This client is generated using `openapi-python-client`:

```bash
# Generate from running service
openapi-python-client generate \
    --url http://localhost:8000/api/v1/openapi.json \
    --output-path src/ticket_client_generated

# Generate from OpenAPI file
openapi-python-client generate \
    --path openapi.json \
    --output-path src/ticket_client_generated
```

## Integration

### With Ticket Client Adapter

The `ticket_client_adapter` package wraps this generated client to provide a clean domain interface:

```python
# Direct generated client usage (HTTP-focused)
from ticket_service_client import Client
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(...)

# Adapter usage (domain-focused)
from ticket_client_adapter import RemoteTicketService
ticket = await service.create_ticket(...)
```

### Custom Configuration

```python
import httpx
from ticket_service_client import Client

# Custom HTTP client configuration
custom_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_connections=100)
)

client = Client(
    base_url="http://localhost:8000",
    httpx_client=custom_client
)
```
