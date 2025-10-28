"""Additional edge case tests for ticket API."""

import pytest
from uuid import uuid4
from ticket_api import Ticket, Comment, TicketPriority, TicketStatus


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_ticket_with_unicode_content(self) -> None:
        """Test ticket with unicode characters."""
        ticket = Ticket(
            title="Bug with émojis 🐛",
            description="Unicode test: café, naïve, résumé",
            reporter="test@example.com"
        )
        assert "émojis 🐛" in ticket.title
        assert "café" in ticket.description

    def test_ticket_boundary_lengths(self) -> None:
        """Test boundary conditions for field lengths."""
        # Test maximum allowed lengths
        max_title = "x" * 200  # Exactly 200 chars
        max_description = "x" * 5000  # Exactly 5000 chars
        
        ticket = Ticket(
            title=max_title,
            description=max_description,
            reporter="test@example.com"
        )
        assert len(ticket.title) == 200
        assert len(ticket.description) == 5000

    def test_comment_boundary_length(self) -> None:
        """Test comment with maximum allowed length."""
        max_content = "x" * 2000  # Exactly 2000 chars
        
        comment = Comment(
            ticket_id=uuid4(),
            author="test@example.com",
            content=max_content
        )
        assert len(comment.content) == 2000

    def test_multiple_comments_on_ticket(self) -> None:
        """Test adding multiple comments to a ticket."""
        ticket = Ticket(
            title="Multi-comment test",
            description="Testing multiple comments",
            reporter="test@example.com"
        )
        
        # Add multiple comments
        ticket = ticket.add_comment("dev1@example.com", "First comment")
        ticket = ticket.add_comment("dev2@example.com", "Second comment")
        ticket = ticket.add_comment("qa@example.com", "Third comment")
        
        assert len(ticket.comments) == 3
        assert ticket.comments[0].content == "First comment"
        assert ticket.comments[1].content == "Second comment"
        assert ticket.comments[2].content == "Third comment"

    def test_ticket_status_transitions(self) -> None:
        """Test various status transitions."""
        ticket = Ticket(
            title="Status test",
            description="Testing status changes",
            reporter="test@example.com"
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
        priorities = [TicketPriority.LOW, TicketPriority.MEDIUM, 
                     TicketPriority.HIGH, TicketPriority.CRITICAL]
        
        for priority in priorities:
            ticket = Ticket(
                title=f"Priority {priority.value} test",
                description="Testing priority levels",
                reporter="test@example.com",
                priority=priority
            )
            assert ticket.priority == priority