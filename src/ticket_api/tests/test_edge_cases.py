"""Additional edge case tests for ticket API."""

from uuid import uuid4

from ticket_api import Comment, Ticket, TicketPriority, TicketStatus

# Constants for boundary values
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5000
MAX_COMMENT_LENGTH = 2000
EXPECTED_COMMENT_COUNT = 3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_ticket_with_unicode_content(self) -> None:
        """Test ticket with unicode characters."""
        ticket = Ticket(
            title="Bug with émojis 🐛",
            description="Unicode test: café, naïve, résumé",
            reporter="test@example.com",
        )
        assert "émojis 🐛" in ticket.title
        assert "café" in ticket.description

    def test_ticket_boundary_lengths(self) -> None:
        """Test boundary conditions for field lengths."""
        # Test maximum allowed lengths
        max_title = "x" * MAX_TITLE_LENGTH
        max_description = "x" * MAX_DESCRIPTION_LENGTH

        ticket = Ticket(
            title=max_title,
            description=max_description,
            reporter="test@example.com",
        )
        assert len(ticket.title) == MAX_TITLE_LENGTH
        assert len(ticket.description) == MAX_DESCRIPTION_LENGTH

    def test_comment_boundary_length(self) -> None:
        """Test comment with maximum allowed length."""
        max_content = "x" * MAX_COMMENT_LENGTH

        comment = Comment(
            ticket_id=uuid4(),
            author="test@example.com",
            content=max_content,
        )
        assert len(comment.content) == MAX_COMMENT_LENGTH

    def test_multiple_comments_on_ticket(self) -> None:
        """Test adding multiple comments to a ticket."""
        ticket = Ticket(
            title="Multi-comment test",
            description="Testing multiple comments",
            reporter="test@example.com",
        )

        # Add multiple comments
        ticket = ticket.add_comment("dev1@example.com", "First comment")
        ticket = ticket.add_comment("dev2@example.com", "Second comment")
        ticket = ticket.add_comment("qa@example.com", "Third comment")

        assert len(ticket.comments) == EXPECTED_COMMENT_COUNT
        assert ticket.comments[0].content == "First comment"
        assert ticket.comments[1].content == "Second comment"
        assert ticket.comments[2].content == "Third comment"

    def test_ticket_status_transitions(self) -> None:
        """Test various status transitions."""
        ticket = Ticket(
            title="Status test",
            description="Testing status changes",
            reporter="test@example.com",
        )

        # Test all status transitions
        ticket = ticket.update_status(TicketStatus.IN_PROGRESS)
        assert ticket.status == TicketStatus.IN_PROGRESS

        ticket = ticket.update_status(TicketStatus.RESOLVED)
        assert ticket.status == TicketStatus.RESOLVED

        ticket = ticket.update_status(TicketStatus.CLOSED)
        assert ticket.status == TicketStatus.CLOSED

        # Can reopen
        ticket = ticket.update_status(TicketStatus.OPEN)
        assert ticket.status == TicketStatus.OPEN

    def test_ticket_priority_levels(self) -> None:
        """Test all priority levels."""
        priorities = [
            TicketPriority.LOW,
            TicketPriority.MEDIUM,
            TicketPriority.HIGH,
            TicketPriority.CRITICAL,
        ]

        for priority in priorities:
            ticket = Ticket(
                title=f"Priority {priority.value} test",
                description="Testing priority levels",
                reporter="test@example.com",
                priority=priority,
            )
            assert ticket.priority == priority

    def test_empty_comments_list(self) -> None:
        """Test ticket with no comments."""
        ticket = Ticket(
            title="No comments",
            description="Testing empty comments",
            reporter="test@example.com",
        )
        assert len(ticket.comments) == 0

    def test_ticket_with_minimal_fields(self) -> None:
        """Test ticket with minimum required fields."""
        ticket = Ticket(
            title="A",
            description="B",
            reporter="a@b.c",
        )
        assert ticket.title == "A"
        assert ticket.description == "B"
        assert ticket.reporter == "a@b.c"

    def test_ticket_immutability_on_update(self) -> None:
        """Test that updating ticket creates new instance."""
        original = Ticket(
            title="Original",
            description="Testing immutability",
            reporter="test@example.com",
        )
        original_id = original.id

        updated = original.update_status(TicketStatus.IN_PROGRESS)

        assert original.status == TicketStatus.OPEN
        assert updated.status == TicketStatus.IN_PROGRESS
        assert original.id == updated.id == original_id
