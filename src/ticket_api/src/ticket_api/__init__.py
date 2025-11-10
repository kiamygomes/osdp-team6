"""Ticket API package - Abstract interface and data models for ticketing microservice.

This package defines the base contract for ticket operations including:
- Data models (Ticket, Comment)
- Abstract service interface (TicketServiceAPI)
- Custom exceptions (ServiceError, TicketNotFoundError)
"""

from .exceptions import ServiceError as ServiceError
from .exceptions import TicketNotFoundError as TicketNotFoundError
from .interface import TicketServiceAPI as TicketServiceAPI
from .models import Comment as Comment
from .models import Ticket as Ticket
from .models import TicketPriority as TicketPriority
from .models import TicketStatus as TicketStatus
