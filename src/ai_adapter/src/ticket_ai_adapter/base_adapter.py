"""Base adapter class with shared functionality for ticket AI adapters.

This module provides common functionality for AI adapters to reduce duplication
and maintain consistent behavior across different AI provider integrations.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from ticket_api import Ticket, TicketPriority, TicketServiceAPI, TicketStatus

from .models import ToolCall, ToolCallType

logger = logging.getLogger(__name__)


class BaseTicketAIAdapter:
    """Base adapter class with shared ticket operation logic.

    This class provides common functionality for:
    - Parameter validation before execution
    - Tool call execution against ticket service
    - Success message formatting
    - Error handling patterns
    """

    def __init__(
        self,
        ticket_service: TicketServiceAPI,
        user_id: str,
        project_key: str | None = None,
    ) -> None:
        """Initialize the base adapter.

        Args:
            ticket_service: Implementation of TicketServiceAPI
            user_id: User identifier for ticket operations
            project_key: Optional Jira project key

        """
        self.ticket_service = ticket_service
        self.user_id = user_id
        self.project_key = project_key

    def _build_system_prompt(self) -> str:
        """Build system prompt for AI with tool calling instructions.

        This is the standardized prompt used across all AI providers.
        """
        return (
            "You are a ticket management assistant that extracts structured information from natural language.\n\n"
            "CRITICAL RULES:\n"
            "1. Extract ONLY the actual ticket title/content, NOT the entire command\n"
            "2. Look for keywords like 'CALLED', 'for', 'to', 'about' to identify the title\n"
            "3. Extract priority from words like 'high', 'low', 'medium', 'urgent'\n"
            "4. Remove command words like 'create', 'make', 'ticket', 'priority' from the title\n\n"
            "Parsing Examples:\n"
            '- Input: "CREATE A high PRIORITY TICKET CALLED im hungry"\n'
            '  Output: {"tool": "create_ticket", "parameters": {"title": "im hungry", "priority": "high"}}\n\n'
            '- Input: "create ticket for fixing login bug with high priority"\n'
            '  Output: {"tool": "create_ticket", "parameters": {"title": "fixing login bug", "priority": "high"}}\n\n'
            '- Input: "make a ticket called update docs"\n'
            '  Output: {"tool": "create_ticket", "parameters": {"title": "update docs", "priority": "medium"}}\n\n'
            '- Input: "urgent ticket about server crash"\n'
            '  Output: {"tool": "create_ticket", "parameters": {"title": "server crash", "priority": "high"}}\n\n'
            "Available tools:\n"
            "- create_ticket: Create a new ticket\n"
            "  Required: title (string - the actual issue/task, NOT the command)\n"
            "  Optional: description (string), priority (low/medium/high, default: medium)\n\n"
            "- list_tickets: List tickets\n"
            "  Optional: status (open/in_progress/closed), limit (number)\n\n"
            "- get_ticket: Get ticket details\n"
            "  Required: ticket_id (string)\n\n"
            "Response format (JSON only, no other text):\n"
            "{\n"
            '  "tool": "create_ticket",\n'
            '  "parameters": {\n'
            '    "title": "extracted title here",\n'
            '    "description": "optional description",\n'
            '    "priority": "high"\n'
            "  }\n"
            "}"
        )

    def _validate_required_params(self, tool_call: ToolCall, required_params: list[str]) -> None:
        """Validate that required parameters are present in the tool call.

        Args:
            tool_call: The tool call to validate
            required_params: List of required parameter names

        Raises:
            ValueError: If any required parameter is missing

        """
        missing_params = [
            param
            for param in required_params
            if param not in tool_call.parameters or not tool_call.parameters[param]
        ]
        if missing_params:
            msg = f"Missing required parameters for {tool_call.type}: {', '.join(missing_params)}"
            raise ValueError(msg)

    def _parse_tool_call_from_dict(self, tool_data: dict[str, object]) -> ToolCall | None:
        """Parse tool call from AI response dictionary.

        Args:
            tool_data: Response data containing tool information

        Returns:
            Parsed ToolCall or None if no valid tool call found

        """
        if "tool" not in tool_data:
            return None

        tool_type_str = tool_data.get("tool")
        parameters = tool_data.get("parameters", {})

        if not isinstance(tool_type_str, str) or not isinstance(parameters, dict):
            return None

        # Map tool name to ToolCallType
        tool_type_map = {
            "create_ticket": ToolCallType.CREATE_TICKET,
            "list_tickets": ToolCallType.LIST_TICKETS,
            "get_ticket": ToolCallType.GET_TICKET,
        }

        tool_type = tool_type_map.get(tool_type_str)
        if not tool_type:
            logger.warning("Unknown tool type: %s", tool_type_str)
            return None

        return ToolCall(type=tool_type, parameters=parameters)

    async def _execute_tool_call(self, tool_call: ToolCall) -> Ticket | list[Ticket] | None:
        """Execute a tool call against the ticket service.

        Args:
            tool_call: The tool call to execute

        Returns:
            Ticket or list of Tickets depending on the operation

        Raises:
            ValueError: If tool type is unsupported or required params missing

        """
        if tool_call.type == ToolCallType.CREATE_TICKET:
            self._validate_required_params(tool_call, ["title"])
            # Description is optional, default to empty string
            priority_str = str(tool_call.parameters.get("priority", "medium"))
            priority = TicketPriority[priority_str.upper()]

            return await self.ticket_service.create_ticket(
                title=str(tool_call.parameters["title"]),
                description=str(tool_call.parameters.get("description", "")),
                priority=priority,
                reporter=self.user_id,
            )

        if tool_call.type == ToolCallType.LIST_TICKETS:
            status_str = tool_call.parameters.get("status")
            status = TicketStatus[str(status_str).upper()] if status_str else None
            limit = int(tool_call.parameters.get("limit", 10))

            return await self.ticket_service.list_tickets(
                assignee=self.user_id,
                status=status,
                limit=limit,
            )

        if tool_call.type == ToolCallType.GET_TICKET:
            self._validate_required_params(tool_call, ["ticket_id"])
            ticket_id = UUID(str(tool_call.parameters["ticket_id"]))
            return await self.ticket_service.get_ticket(ticket_id)

        msg = f"Unsupported tool type: {tool_call.type}"
        raise ValueError(msg)

    def _format_success_message(
        self,
        tool_type: ToolCallType,
        result_data: Ticket | list[Ticket] | None,
    ) -> str:
        """Format success message based on tool type.

        Args:
            tool_type: The type of tool that was executed
            result_data: The result from the tool execution

        Returns:
            Formatted success message

        """
        messages = {
            ToolCallType.CREATE_TICKET: (
                f"Created ticket: {result_data.title}"
                if isinstance(result_data, Ticket)
                else "Created ticket successfully"
            ),
            ToolCallType.LIST_TICKETS: (
                f"Found {len(result_data)} tickets"
                if isinstance(result_data, list)
                else "Retrieved tickets successfully"
            ),
            ToolCallType.GET_TICKET: (
                f"Retrieved ticket: {result_data.title}"
                if isinstance(result_data, Ticket)
                else "Retrieved ticket successfully"
            ),
        }
        return messages.get(tool_type, "Operation completed successfully")

    def _parse_response_to_dict(self, response: object) -> dict[str, object] | None:
        """Parse AI response to dictionary format.

        Args:
            response: Response from AI service (dict or JSON string)

        Returns:
            Parsed dictionary or None if parsing fails

        """
        if isinstance(response, dict):
            # Runtime check ensures this is actually a dict
            return dict(response)
        if isinstance(response, str):
            try:
                parsed = json.loads(response)
                if not isinstance(parsed, dict):
                    logger.warning("JSON response is not a dictionary: %s", type(parsed))
                    return None
                return dict(parsed)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response: %s", response)
                return None
        return None
