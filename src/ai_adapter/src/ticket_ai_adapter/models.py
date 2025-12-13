"""Data models for AI adapter operations."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ToolCallType(str, Enum):
    """Types of tool calls supported by the AI adapter."""

    CREATE_TICKET = "create_ticket"
    GET_TICKET = "get_ticket"
    LIST_TICKETS = "list_tickets"
    UPDATE_TICKET = "update_ticket"
    DELETE_TICKET = "delete_ticket"
    ADD_COMMENT = "add_comment"
    UPDATE_STATUS = "transition_status"
    REASSIGN_TICKET = "reassign_ticket"


@dataclass
class ToolCall:
    """Represents a structured tool call parsed from AI response."""

    type: ToolCallType
    parameters: dict[str, Any]


@dataclass
class CommandResult:
    """Result of processing a natural language command."""

    success: bool
    message: str
    data: Any | None = None
    error: str | None = None
