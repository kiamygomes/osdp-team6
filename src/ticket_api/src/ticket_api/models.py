"""Data models for the ticket API using Pydantic.

This module defines the core data structures used throughout the ticketing system.
"""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TicketStatus(str, Enum):
    """Enumeration of possible ticket statuses."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Enumeration of ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Comment(BaseModel):
    """Represents a comment on a ticket.

    Comments are immutable once created and track who made the comment
    and when it was created.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the comment")
    ticket_id: UUID = Field(description="ID of the ticket this comment belongs to")
    author: str = Field(description="Username or email of the comment author")
    content: str = Field(min_length=1, max_length=2000, description="Comment text content")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the comment was created",
    )

    model_config = ConfigDict(frozen=True)  # Make comments immutable


class Ticket(BaseModel):
    """Represents a support ticket in the system.

    Tickets track issues, requests, or tasks with associated metadata
    like status, priority, and timestamps.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the ticket")
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Brief title describing the ticket",
    )
    description: str = Field(
        min_length=1,
        max_length=5000,
        description="Detailed description of the ticket",
    )
    status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        description="Current status of the ticket",
    )
    priority: TicketPriority = Field(
        default=TicketPriority.MEDIUM,
        description="Priority level of the ticket",
    )
    assignee: str | None = Field(default=None, description="Username or email of assigned person")
    reporter: str = Field(description="Username or email of the person who created the ticket")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the ticket was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the ticket was last updated",
    )
    comments: list[Comment] = Field(
        default_factory=list,
        description="List of comments on this ticket",
    )

    def add_comment(self, author: str, content: str) -> "Ticket":
        """Add a new comment to the ticket.

        Args:
            author: Username or email of the comment author
            content: Comment text content

        Returns:
            New Ticket instance with the comment added

        """
        new_comment = Comment(
            ticket_id=self.id,
            author=author,
            content=content,
        )

        # Create a new ticket instance with updated comments and timestamp
        return self.model_copy(
            update={
                "comments": [*self.comments, new_comment],
                "updated_at": datetime.now(UTC),
            },
        )

    def update_status(self, new_status: TicketStatus) -> "Ticket":
        """Update the ticket status.

        Args:
            new_status: New status to set

        Returns:
            New Ticket instance with updated status

        """
        return self.model_copy(
            update={
                "status": new_status,
                "updated_at": datetime.now(UTC),
            },
        )

    def assign_to(self, assignee: str) -> "Ticket":
        """Assign the ticket to a person.

        Args:
            assignee: Username or email of the person to assign to

        Returns:
            New Ticket instance with updated assignee

        """
        return self.model_copy(
            update={
                "assignee": assignee,
                "updated_at": datetime.now(UTC),
            },
        )
