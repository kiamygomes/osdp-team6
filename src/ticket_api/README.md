# Ticket API

This package defines the abstract interface and data models for the ticketing microservice. It serves as the base contract that all implementations must follow.

## Components

### Models (`models.py`)

- **`TicketStatus`**: Enum for ticket statuses (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- **`TicketPriority`**: Enum for priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- **`Comment`**: Immutable comment model with validation
- **`Ticket`**: Main ticket model with methods for updates

### Interface (`interface.py`)

- **`TicketServiceAPI`**: Abstract base class defining the service contract
  - `create_ticket()`: Create new tickets
  - `get_ticket()`: Retrieve tickets by ID
  - `list_tickets()`: List tickets with filtering
  - `update_ticket()`: Update existing tickets
  - `delete_ticket()`: Delete tickets
  - `add_comment()`: Add comments to tickets
  - `get_ticket_comments()`: Retrieve ticket comments

## Features

- **Type Safety**: Full type hints throughout
- **Validation**: Pydantic models with field validation
- **Immutability**: Comments are immutable once created
- **Extensibility**: Easy to extend with new fields or methods
- **Documentation**: Comprehensive docstrings for all methods

## Usage

```python
from ticket_api import Ticket, Comment, TicketServiceAPI, TicketStatus, TicketPriority

# Create a ticket
ticket = Ticket(
    title="Bug in login system",
    description="Users cannot log in with valid credentials",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)

# Add a comment
updated_ticket = ticket.add_comment("dev@example.com", "Investigating the issue")

# Implement the service interface
class MyTicketService(TicketServiceAPI):
    async def create_ticket(self, title, description, reporter, priority=TicketPriority.MEDIUM, assignee=None):
        # Your implementation here
        pass
    # ... implement other methods
```

## Testing

Run the API contract tests:

```bash
uv run pytest src/ticket_api/tests/ -v
```