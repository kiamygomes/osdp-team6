"""Tests for the ticket API contract.

This module tests the data models and ensures the abstract interface
cannot be instantiated directly.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ticket_api.interface import TicketServiceAPI
from ticket_api.models import Comment, Ticket, TicketPriority, TicketStatus


class TestTicketModel:
    """Test cases for the Ticket data model."""

    def test_ticket_creation_with_defaults(self) -> None:
        """Test creating a ticket with minimal required fields."""
        ticket = Ticket(
            title="Test ticket",
            description="This is a test ticket",
            reporter="test@example.com",
        )

        assert ticket.title == "Test ticket"
        assert ticket.description == "This is a test ticket"
        assert ticket.reporter == "test@example.com"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.MEDIUM
        assert ticket.assignee is None
        assert isinstance(ticket.id, UUID)
        assert isinstance(ticket.created_at, datetime)
        assert isinstance(ticket.updated_at, datetime)
        assert ticket.comments == []

    def test_ticket_creation_with_all_fields(self) -> None:
        """Test creating a ticket with all fields specified."""
        ticket_id = uuid4()
        created_time = datetime.now(UTC)

        ticket = Ticket(
            id=ticket_id,
            title="High priority bug",
            description="Critical system failure",
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.CRITICAL,
            assignee="dev@example.com",
            reporter="user@example.com",
            created_at=created_time,
            updated_at=created_time,
        )

        assert ticket.id == ticket_id
        assert ticket.title == "High priority bug"
        assert ticket.description == "Critical system failure"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.priority == TicketPriority.CRITICAL
        assert ticket.assignee == "dev@example.com"
        assert ticket.reporter == "user@example.com"
        assert ticket.created_at == created_time
        assert ticket.updated_at == created_time

    def test_ticket_validation_empty_title(self) -> None:
        """Test that empty title raises validation error."""
        with pytest.raises(ValidationError):
            Ticket(
                title="",
                description="Valid description",
                reporter="test@example.com",
            )

    def test_ticket_validation_empty_description(self) -> None:
        """Test that empty description raises validation error."""
        with pytest.raises(ValidationError):
            Ticket(
                title="Valid title",
                description="",
                reporter="test@example.com",
            )

    def test_ticket_validation_title_too_long(self) -> None:
        """Test that overly long title raises validation error."""
        long_title = "x" * 201  # Exceeds 200 character limit

        with pytest.raises(ValidationError):
            Ticket(
                title=long_title,
                description="Valid description",
                reporter="test@example.com",
            )

    def test_ticket_validation_description_too_long(self) -> None:
        """Test that overly long description raises validation error."""
        long_description = "x" * 5001  # Exceeds 5000 character limit

        with pytest.raises(ValidationError):
            Ticket(
                title="Valid title",
                description=long_description,
                reporter="test@example.com",
            )

    def test_ticket_add_comment(self) -> None:
        """Test adding a comment to a ticket."""
        ticket = Ticket(
            title="Test ticket",
            description="This is a test ticket",
            reporter="test@example.com",
        )

        updated_ticket = ticket.add_comment("commenter@example.com", "This is a comment")

        assert len(updated_ticket.comments) == 1
        assert updated_ticket.comments[0].author == "commenter@example.com"
        assert updated_ticket.comments[0].content == "This is a comment"
        assert updated_ticket.comments[0].ticket_id == ticket.id
        assert updated_ticket.updated_at > ticket.updated_at

        # Original ticket should be unchanged
        assert len(ticket.comments) == 0

    def test_ticket_update_status(self) -> None:
        """Test updating ticket status."""
        ticket = Ticket(
            title="Test ticket",
            description="This is a test ticket",
            reporter="test@example.com",
        )

        updated_ticket = ticket.update_status(TicketStatus.RESOLVED)

        assert updated_ticket.status == TicketStatus.RESOLVED
        assert updated_ticket.updated_at > ticket.updated_at

        # Original ticket should be unchanged
        assert ticket.status == TicketStatus.OPEN

    def test_ticket_assign_to(self) -> None:
        """Test assigning a ticket to someone."""
        ticket = Ticket(
            title="Test ticket",
            description="This is a test ticket",
            reporter="test@example.com",
        )

        updated_ticket = ticket.assign_to("assignee@example.com")

        assert updated_ticket.assignee == "assignee@example.com"
        assert updated_ticket.updated_at > ticket.updated_at

        # Original ticket should be unchanged
        assert ticket.assignee is None


class TestCommentModel:
    """Test cases for the Comment data model."""

    def test_comment_creation(self) -> None:
        """Test creating a comment with all required fields."""
        ticket_id = uuid4()
        comment = Comment(
            ticket_id=ticket_id,
            author="commenter@example.com",
            content="This is a test comment",
        )

        assert comment.ticket_id == ticket_id
        assert comment.author == "commenter@example.com"
        assert comment.content == "This is a test comment"
        assert isinstance(comment.id, UUID)
        assert isinstance(comment.created_at, datetime)

    def test_comment_validation_empty_content(self) -> None:
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError):
            Comment(
                ticket_id=uuid4(),
                author="commenter@example.com",
                content="",
            )

    def test_comment_validation_content_too_long(self) -> None:
        """Test that overly long content raises validation error."""
        long_content = "x" * 2001  # Exceeds 2000 character limit

        with pytest.raises(ValidationError):
            Comment(
                ticket_id=uuid4(),
                author="commenter@example.com",
                content=long_content,
            )

    def test_comment_immutability(self) -> None:
        """Test that comments are immutable once created."""
        comment = Comment(
            ticket_id=uuid4(),
            author="commenter@example.com",
            content="This is a test comment",
        )

        # Attempting to modify should raise an error
        with pytest.raises(ValidationError, match="Instance is frozen"):
            comment.content = "Modified content"


class TestTicketServiceAPI:
    """Test cases for the TicketServiceAPI abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that TicketServiceAPI cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TicketServiceAPI()  # type: ignore[abstract]

    def test_concrete_implementation_must_implement_all_methods(self) -> None:
        """Test that concrete implementations must implement all abstract methods."""

        class IncompleteImplementation(TicketServiceAPI):  # type: ignore[misc]
            """Incomplete implementation missing some methods."""

            async def create_ticket(
                self,
                title: str,
                description: str,
                reporter: str,
                priority: TicketPriority = TicketPriority.MEDIUM,
                assignee: str | None = None,
            ) -> Ticket:
                return Ticket(title=title, description=description, reporter=reporter)

            # Missing other required methods

        # Should not be able to instantiate incomplete implementation
        with pytest.raises(TypeError):
            IncompleteImplementation()  # type: ignore[abstract]

    def test_complete_implementation_can_be_instantiated(self) -> None:
        """Test that complete implementations can be instantiated."""

        class CompleteImplementation(TicketServiceAPI):
            """Complete implementation with all required methods."""

            async def create_ticket(
                self,
                title: str,
                description: str,
                reporter: str,
                priority: TicketPriority = TicketPriority.MEDIUM,
                assignee: str | None = None,
            ) -> Ticket:
                return Ticket(
                    title=title,
                    description=description,
                    reporter=reporter,
                    priority=priority,
                    assignee=assignee,
                )

            async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
                return None

            async def list_tickets(
                self,
                status: TicketStatus | None = None,
                assignee: str | None = None,
                reporter: str | None = None,
                limit: int = 100,
                offset: int = 0,
            ) -> list[Ticket]:
                return []

            async def update_ticket(  # noqa: PLR0913
                self,
                ticket_id: UUID,
                title: str | None = None,
                description: str | None = None,
                status: TicketStatus | None = None,
                priority: TicketPriority | None = None,
                assignee: str | None = None,
            ) -> Ticket | None:
                return None

            async def delete_ticket(self, ticket_id: UUID) -> bool:
                return False

            async def add_comment(
                self, ticket_id: UUID, author: str, content: str
            ) -> Comment | None:
                return None

            async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]:
                return []

        # Should be able to instantiate complete implementation
        service = CompleteImplementation()
        assert isinstance(service, TicketServiceAPI)


class TestEnums:
    """Test cases for the enum classes."""

    def test_ticket_status_values(self) -> None:
        """Test that TicketStatus has expected values."""
        assert TicketStatus.OPEN.value == "open"
        assert TicketStatus.IN_PROGRESS.value == "in_progress"
        assert TicketStatus.RESOLVED.value == "resolved"
        assert TicketStatus.CLOSED.value == "closed"

    def test_ticket_priority_values(self) -> None:
        """Test that TicketPriority has expected values."""
        assert TicketPriority.LOW.value == "low"
        assert TicketPriority.MEDIUM.value == "medium"
        assert TicketPriority.HIGH.value == "high"
        assert TicketPriority.CRITICAL.value == "critical"
