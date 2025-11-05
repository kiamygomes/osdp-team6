"""Edge-case unit tests for Ticket and Comment models."""

from uuid import uuid4

from ticket_api.models import Comment, Ticket, TicketPriority, TicketStatus

# Constants for boundary values
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000


class TestEdgeCases:
    """Test boundary conditions and model field limits."""

    def test_ticket_boundary_lengths(self) -> None:
        """Ticket accepts maximum allowed field lengths."""
        max_title = "x" * MAX_TITLE_LENGTH
        max_description = "y" * MAX_DESCRIPTION_LENGTH

        ticket = Ticket(
            title=max_title,
            description=max_description,
            reporter="test@example.com",
        )

        assert len(ticket.title) == MAX_TITLE_LENGTH
        assert len(ticket.description) == MAX_DESCRIPTION_LENGTH
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == TicketPriority.MEDIUM

    def test_comment_boundary_length(self) -> None:
        """Comment accepts maximum allowed content length."""
        max_content = "x" * MAX_COMMENT_LENGTH

        comment = Comment(
            ticket_id=uuid4(),
            author="author@example.com",
            content=max_content,
        )

        assert len(comment.content) == MAX_COMMENT_LENGTH
        assert comment.author == "author@example.com"

    def test_empty_comments_list_default(self) -> None:
        """Ticket initializes with an empty comments list."""
        ticket = Ticket(
            title="No comments",
            description="Testing default empty comments",
            reporter="test@example.com",
        )

        assert isinstance(ticket.comments, list)
        assert len(ticket.comments) == 0

    def test_ticket_minimal_fields(self) -> None:
        """Ticket with minimal required fields is valid."""
        ticket = Ticket(
            title="A",
            description="B",
            reporter="a@b.c",
        )

        assert ticket.title == "A"
        assert ticket.description == "B"
        assert ticket.reporter == "a@b.c"
        assert ticket.priority == TicketPriority.MEDIUM
        assert ticket.status == TicketStatus.OPEN
