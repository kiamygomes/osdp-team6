"""Custom exceptions for the Ticket API."""

from uuid import UUID


class TicketAPIError(Exception):
    """Base exception for all ticket API errors."""


class ServiceError(TicketAPIError):
    """Generic error raised when a service operation fails."""


class TicketNotFoundError(TicketAPIError):
    """Raised when a ticket could not be found."""

    def __init__(self, ticket_id: UUID) -> None:
        """Initialize with the ticket ID that was not found."""
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")


class InvalidCommandError(TicketAPIError):
    """Raised when an operation violates a business rule or has invalid input."""
