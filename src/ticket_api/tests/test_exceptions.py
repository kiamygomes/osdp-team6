"""Unit tests for custom exceptions in the ticket API."""

from uuid import uuid4

import pytest

from ticket_api.exceptions import ServiceError, TicketAPIError, TicketNotFoundError


class TestTicketAPIError:
    """Base exception tests."""

    def test_can_be_raised_and_caught(self) -> None:
        """TicketAPIError can be raised and caught."""
        error_msg = "Test error"
        with pytest.raises(TicketAPIError):
            raise TicketAPIError(error_msg)

    def test_inherits_from_exception(self) -> None:
        """TicketAPIError inherits from Exception."""
        assert issubclass(TicketAPIError, Exception)


class TestTicketNotFoundError:
    """Tests for TicketNotFoundError behavior."""

    def test_stores_ticket_id_and_message(self) -> None:
        """TicketNotFoundError stores ticket ID and includes it in message."""
        ticket_id = uuid4()
        error = TicketNotFoundError(ticket_id)
        assert error.ticket_id == ticket_id
        assert str(ticket_id) in str(error)
        assert "not found" in str(error).lower()

    def test_raises_and_caught_as_base_error(self) -> None:
        """TicketNotFoundError can be caught as TicketAPIError."""
        ticket_id = uuid4()
        with pytest.raises(TicketAPIError):
            raise TicketNotFoundError(ticket_id)


class TestServiceError:
    """Tests for ServiceError inheritance and message."""

    def test_inherits_from_ticket_api_error(self) -> None:
        """ServiceError inherits from TicketAPIError."""
        assert issubclass(ServiceError, TicketAPIError)

    def test_message_preserved(self) -> None:
        """ServiceError preserves the error message."""
        error = ServiceError("Service failed")
        assert "Service failed" in str(error)
