# Ticket API

Core abstract interface and data models for the ticketing system.

## Interface

::: ticket_api.interface.TicketServiceAPI

## Models

::: ticket_api.models.Ticket

::: ticket_api.models.Comment

::: ticket_api.models.TicketStatus

::: ticket_api.models.TicketPriority

## Usage

```python
from ticket_api import TicketServiceAPI, Ticket, TicketPriority

# Implement the interface
class MyTicketService(TicketServiceAPI):
    async def create_ticket(self, title: str, description: str, reporter: str) -> Ticket:
        # Implementation logic
        pass

# Work with models
ticket = Ticket(
    title="Bug Report",
    description="Issue description",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)

# Add comment (returns new instance)
updated_ticket = ticket.add_comment("author", "comment content")
```