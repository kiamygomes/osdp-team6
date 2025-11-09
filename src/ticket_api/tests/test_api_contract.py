"""Unit tests for the ticket API models and abstract interface.

Covers:
- Data model structure and defaults
- Enum value integrity
- Abstract service contract compliance
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ticket_api.interface import TicketServiceAPI
from ticket_api.models import Comment, Ticket, TicketPriority, TicketStatus

# ======================================================================
# Ticket Model Tests
# ======================================================================


class TestTicketModel:
    """Unit tests for the Ticket data model (structure & validation only)."""

    def test_ticket_creation_with_defaults(self) -> None:
        """Test creating a ticket with default values."""
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
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.priority == TicketPriority.CRITICAL
        assert ticket.assignee == "dev@example.com"
        assert ticket.reporter == "user@example.com"
        assert ticket.created_at == created_time
        assert ticket.updated_at == created_time

    def test_ticket_accepts_various_field_lengths(self) -> None:
        """Dataclass accepts various field lengths (validation happens at service layer)."""
        max_title_len = 201
        max_desc_len = 5001

        # Empty strings are accepted by dataclass
        ticket1 = Ticket(title="", description="desc", reporter="a@b.com")
        assert ticket1.title == ""

        # Long strings are accepted by dataclass
        ticket2 = Ticket(title="x" * max_title_len, description="desc", reporter="a@b.com")
        assert len(ticket2.title) == max_title_len

        ticket3 = Ticket(title="Valid", description="x" * max_desc_len, reporter="a@b.com")
        assert len(ticket3.description) == max_desc_len


# ======================================================================
# Comment Model Tests
# ======================================================================


class TestCommentModel:
    """Unit tests for the Comment data model."""

    def test_comment_creation(self) -> None:
        """Test creating a comment with required fields."""
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

    def test_comment_immutability(self) -> None:
        """Comment is frozen and cannot be modified after creation."""
        comment = Comment(ticket_id=uuid4(), author="c@example.com", content="ok")
        with pytest.raises(AttributeError):
            comment.content = "modified"  # type: ignore[misc]

    def test_comment_accepts_various_content_lengths(self) -> None:
        """Dataclass accepts various content lengths (validation happens at service layer)."""
        max_content_len = 2001

        # Empty content is accepted by dataclass
        comment1 = Comment(ticket_id=uuid4(), author="commenter@example.com", content="")
        assert comment1.content == ""

        # Long content is accepted by dataclass
        comment2 = Comment(
            ticket_id=uuid4(),
            author="commenter@example.com",
            content="x" * max_content_len,
        )
        assert len(comment2.content) == max_content_len


# ======================================================================
# Abstract Interface Tests
# ======================================================================


class _CompleteTestImplementation(TicketServiceAPI):
    """Test implementation with all required methods."""

    async def create_ticket(self, *_args: object, **kwargs: object) -> Ticket:
        # Type-safe construction: extract known fields with proper types
        title = str(kwargs.get("title", ""))
        description = str(kwargs.get("description", ""))
        reporter = str(kwargs.get("reporter", ""))
        return Ticket(title=title, description=description, reporter=reporter)

    async def get_ticket(self, _ticket_id: UUID) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def update_ticket(
        self,
        _ticket_id: UUID,
        _title: str | None = None,
        _description: str | None = None,
        _status: TicketStatus | None = None,
        _priority: TicketPriority | None = None,
        _assignee: str | None = None,
    ) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def list_tickets(
        self,
        _status: TicketStatus | None = None,
        _assignee: str | None = None,
        _reporter: str | None = None,
        _limit: int = 100,
        _offset: int = 0,
    ) -> list[Ticket]:
        return []

    async def delete_ticket(self, _ticket_id: UUID) -> bool:
        return True

    async def transition_status(self, _ticket_id: UUID, _new_status: TicketStatus) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def reassign_ticket(self, _ticket_id: UUID, _new_assignee: str) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def update_description(self, _ticket_id: UUID, _new_description: str) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def update_priority(self, _ticket_id: UUID, _new_priority: TicketPriority) -> Ticket:
        return Ticket(title="t", description="d", reporter="r")

    async def add_comment(self, ticket_id: UUID, author: str, content: str) -> Comment:
        return Comment(ticket_id=ticket_id, author=author, content=content)

    async def get_ticket_comments(self, _ticket_id: UUID) -> list[Comment]:
        return []


class TestTicketServiceAPI:
    """Unit tests for the TicketServiceAPI abstract contract."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """The abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TicketServiceAPI()  # type: ignore[abstract]

    def test_incomplete_implementation_fails_instantiation(self) -> None:
        """Subclasses missing methods should raise TypeError."""

        class IncompleteImplementation(TicketServiceAPI):  # type: ignore[misc]
            async def create_ticket(self, *_args: object, **_kwargs: object) -> Ticket:  # type: ignore[override]
                return Ticket(title="x", description="y", reporter="z")  # pragma: no cover

        with pytest.raises(TypeError):
            IncompleteImplementation()  # type: ignore[abstract]

    def test_complete_implementation_can_instantiate(self) -> None:
        """Fully implemented subclass should instantiate successfully."""
        service = _CompleteTestImplementation()
        assert isinstance(service, TicketServiceAPI)

    async def test_complete_implementation_methods_callable(self) -> None:
        """All methods in complete implementation can be called."""
        service = _CompleteTestImplementation()
        ticket_id = uuid4()

        # Test all methods are callable
        ticket = await service.create_ticket(title="t", description="d", reporter="r")
        assert isinstance(ticket, Ticket)

        ticket = await service.get_ticket(ticket_id)
        assert isinstance(ticket, Ticket)

        tickets = await service.list_tickets()
        assert isinstance(tickets, list)

        result = await service.delete_ticket(ticket_id)
        assert isinstance(result, bool)

        ticket = await service.transition_status(ticket_id, TicketStatus.OPEN)
        assert isinstance(ticket, Ticket)

        ticket = await service.reassign_ticket(ticket_id, "user@example.com")
        assert isinstance(ticket, Ticket)

        ticket = await service.update_description(ticket_id, "new desc")
        assert isinstance(ticket, Ticket)

        ticket = await service.update_priority(ticket_id, TicketPriority.HIGH)
        assert isinstance(ticket, Ticket)

        comment = await service.add_comment(ticket_id, "author@example.com", "content")
        assert isinstance(comment, Comment)

        comments = await service.get_ticket_comments(ticket_id)
        assert isinstance(comments, list)


# ======================================================================
# Enum Tests
# ======================================================================


class TestEnums:
    """Unit tests for enums."""

    def test_ticket_status_values(self) -> None:
        """Test that TicketStatus enum has expected values."""
        expected = {"open", "in_progress", "resolved", "closed"}
        assert {s.value for s in TicketStatus} == expected

    def test_ticket_priority_values(self) -> None:
        """Test that TicketPriority enum has expected values."""
        expected = {"low", "medium", "high", "critical"}
        assert {p.value for p in TicketPriority} == expected
