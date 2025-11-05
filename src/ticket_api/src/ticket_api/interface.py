"""Abstract base class defining the ticket service API contract.

This module defines the interface that all ticket service implementations
must follow, ensuring consistency across different implementations.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from .models import Comment, Ticket, TicketPriority, TicketStatus


class TicketServiceAPI(ABC):
    """Abstract base class for ticket service implementations.

    This interface defines all the operations that a ticket service
    must support. Concrete implementations must provide all these methods.
    """

    # Creation & retrieval
    @abstractmethod
    async def create_ticket(
        self,
        title: str,
        description: str,
        reporter: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a new ticket in the system."""

    @abstractmethod
    async def get_ticket(
        self,
        ticket_id: UUID,
    ) -> Ticket:
        """Retrieve a ticket by its ID."""

    @abstractmethod
    async def list_tickets(
        self,
        status: TicketStatus | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """List tickets with optional filtering."""

    # Workflow / lifecycle
    @abstractmethod
    async def transition_status(
        self,
        ticket_id: UUID,
        new_status: TicketStatus,
    ) -> Ticket:
        """Transition the ticket to a new status (e.g., open → resolved)."""

    @abstractmethod
    async def reassign_ticket(
        self,
        ticket_id: UUID,
        new_assignee: str,
    ) -> Ticket:
        """Assign a ticket to a new user."""

    @abstractmethod
    async def update_priority(
        self,
        ticket_id: UUID,
        new_priority: TicketPriority,
    ) -> Ticket:
        """Change the priority level of a ticket."""

    @abstractmethod
    async def update_description(
        self,
        ticket_id: UUID,
        new_description: str,
    ) -> Ticket:
        """Edit the description of a ticket."""

    # Collaboration
    @abstractmethod
    async def add_comment(
        self,
        ticket_id: UUID,
        author: str,
        content: str,
    ) -> Comment:
        """Add a comment to an existing ticket."""

    @abstractmethod
    async def get_ticket_comments(
        self,
        ticket_id: UUID,
    ) -> list[Comment]:
        """Retrieve all comments for a given ticket."""

    # Maintenance
    @abstractmethod
    async def delete_ticket(
        self,
        ticket_id: UUID,
    ) -> bool:
        """Delete a ticket."""
