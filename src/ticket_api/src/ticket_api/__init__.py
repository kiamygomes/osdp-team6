"""Ticket API package - Abstract interface and data models for ticketing microservice.

This package defines the base contract for ticket operations including:
- Data models (Ticket, Comment)
- Abstract service interface (TicketServiceAPI)
"""

from .interface import TicketServiceAPI
from .models import Comment, Ticket, TicketPriority, TicketStatus

__all__ = ["Comment", "Ticket", "TicketPriority", "TicketServiceAPI", "TicketStatus"]
