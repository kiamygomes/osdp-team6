# Ticket API

Abstract interface and data models for ticketing operations.

## Overview

- **Package**: `ticket_api`
- **Purpose**: Define contract for all implementations
- **Dependencies**: None (stdlib only)
- **Coverage**: 100% (22 tests)

## Key Features

- Zero external dependencies
- Immutable frozen dataclasses
- Full type hints
- Custom exception hierarchy

## Interface

`TicketServiceAPI` - Abstract base class with 10 required methods:

- `create_ticket()` - Create new ticket
- `get_ticket()` - Get by ID
- `list_tickets()` - List with filters
- `update_ticket()` - Update fields
- `delete_ticket()` - Delete ticket
- `add_comment()` - Add comment
- `get_ticket_comments()` - Get comments
- `transition_status()` - Change status
- `reassign_ticket()` - Change assignee
- `update_priority()` - Change priority
- `update_description()` - Update description

## Data Models

**Ticket** - Frozen dataclass with id, title, description, status, priority, assignee, reporter, timestamps, comments

**Comment** - Frozen dataclass with id, ticket_id, author, content, created_at

## Enums

- `TicketStatus`: OPEN, IN_PROGRESS, RESOLVED, CLOSED
- `TicketPriority`: LOW, MEDIUM, HIGH, CRITICAL

## Exceptions

- `ServiceError` - Base exception for service errors
- `TicketNotFoundError` - Ticket not found (extends ServiceError)

## Usage

```python
from ticket_api import TicketServiceAPI, Ticket, TicketPriority

class MyService(TicketServiceAPI):
    async def create_ticket(self, title, description, reporter, 
                          priority=TicketPriority.MEDIUM, assignee=None):
        # Implementation
        pass
```

## Related

- [ticket_impl](ticket_impl.md) - Jira implementation
- [ticket_client_adapter](ticket_client_adapter.md) - Remote HTTP implementation
