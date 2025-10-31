# Ticket Client Adapter

Adapter that wraps the generated HTTP client and exposes it through the `TicketServiceAPI` interface.

## Features

- Implements `TicketServiceAPI` interface for remote service access
- Hides HTTP/network details from business logic
- Model conversion between HTTP and domain models
- Connection management and error translation

## Components

::: ticket_client_adapter.client.RemoteTicketService

## Usage

```python
from ticket_client_adapter import RemoteTicketService
from ticket_api import TicketPriority, TicketStatus

# Use as context manager for automatic connection cleanup
async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="your-user-id",
    project_key="PROJ"
) as service:
    
    # Clean domain interface - no HTTP details!
    ticket = await service.create_ticket(
        title="Bug Report",
        description="Found an issue",
        reporter="user@example.com",
        priority=TicketPriority.HIGH
    )
    
    # List tickets with domain filters
    tickets = await service.list_tickets(
        status=TicketStatus.OPEN,
        assignee="dev@example.com"
    )
    
    # Add comment
    comment = await service.add_comment(
        ticket_id=ticket.id,
        author="support@example.com",
        content="Investigating this issue"
    )
```

## Pattern

Implements the Adapter Pattern to bridge HTTP client and domain interface:

```
Domain Layer (ticket_api)
    ↓
Adapter Layer (ticket_client_adapter) 
    ↓
Generated Client (ticket_client_generated)
    ↓
HTTP Layer (httpx)
```