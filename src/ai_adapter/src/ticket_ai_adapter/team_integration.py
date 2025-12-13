"""Integration adapters that use other teams' AI service packages.

This module demonstrates the Second Submission requirement:
- Integration with Claude team's AI service (via ai_chat_adapter)
- Integration with OpenAI team's AI service (via ai_adapter)
- Both integrated with our Jira Ticket Service
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from ticket_api import Ticket, TicketPriority, TicketServiceAPI, TicketStatus

from .models import CommandResult, ToolCall, ToolCallType

if TYPE_CHECKING:
    from ai_api import AIInterface as OpenAIInterface
    from ai_chat_api import AIInterface as ClaudeInterface

logger = logging.getLogger(__name__)


class ClaudeTeamAdapter:
    """Adapter using Claude team's ai_chat_api for ticket operations.

    This demonstrates integration with the Claude team's repository:
    https://github.com/shichenz1999/oss-taapp/tree/hw3
    """

    def __init__(
        self,
        ticket_service: TicketServiceAPI,
        user_id: str,
        project_key: str | None = None,
    ) -> None:
        """Initialize adapter with Claude team's AI interface.

        Args:
            ticket_service: Jira ticket service implementation
            user_id: User ID for ticket operations
            project_key: Optional Jira project key

        """
        from ai_chat_api import get_ai_interface

        self.ticket_service = ticket_service
        self.user_id = user_id
        self.project_key = project_key
        self.ai_client: ClaudeInterface = get_ai_interface()
        self._system_prompt = self._build_system_prompt()
        logger.info("Claude team's AI interface initialized successfully")

    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude with tool calling instructions."""
        return (
            "You are a ticket management assistant. "
            "Parse user requests and respond with JSON tool calls.\n\n"
            "Available tools:\n"
            "- create_ticket: Create a new ticket\n"
            "  Parameters: title (string), description (string), "
            "priority (low/medium/high)\n\n"
            "- list_tickets: List tickets\n"
            "  Parameters: status (open/in_progress/done), limit (number)\n\n"
            "- get_ticket: Get ticket details\n"
            "  Parameters: ticket_id (string)\n\n"
            "Respond ONLY with JSON in this format:\n"
            "{\n"
            '  "tool": "create_ticket",\n'
            '  "parameters": {\n'
            '    "title": "Bug title",\n'
            '    "description": "Bug description",\n'
            '    "priority": "high"\n'
            "  }\n"
            "}"
        )

    async def process_command(self, prompt: str) -> CommandResult:
        """Process natural language command using Claude team's AI service.

        Args:
            prompt: Natural language command from user

        Returns:
            CommandResult with execution status

        """
        try:
            # Call Claude team's AI service with tool calling schema
            tool_schema = {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "parameters": {"type": "object"},
                },
                "required": ["tool", "parameters"],
            }

            response = self.ai_client.generate_response(
                user_input=prompt,
                system_prompt=self._system_prompt,
                response_schema=tool_schema,
            )

            # Parse the tool call
            if isinstance(response, dict):
                tool_data = response
            elif isinstance(response, str):
                tool_data = json.loads(response)
            else:
                return CommandResult(
                    success=False,
                    message="Invalid response from AI service",
                    error=f"Expected dict or str, got {type(response).__name__}",
                )

            tool_call = self._parse_tool_call(tool_data)
            if not tool_call:
                return CommandResult(
                    success=True,
                    message=str(response),
                )

            # Execute the tool call
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except Exception:
            logger.exception("Error processing command with Claude team's service")
            return CommandResult(
                success=False,
                message="Failed to process command",
                error="An error occurred while processing the command",
            )

    def _parse_tool_call(self, tool_data: dict[str, object]) -> ToolCall | None:
        """Parse tool call from Claude's response.

        Args:
            tool_data: Response data from Claude containing tool information

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
            return None

        return ToolCall(type=tool_type, parameters=parameters)

    async def _execute_tool_call(self, tool_call: ToolCall) -> Ticket | list[Ticket] | None:
        """Execute a tool call against the ticket service.

        Args:
            tool_call: The tool call to execute

        Returns:
            Ticket or list of Tickets depending on the operation

        Raises:
            ValueError: If tool type is unsupported

        """
        if tool_call.type == ToolCallType.CREATE_TICKET:
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


class OpenAITeamAdapter:
    """Adapter using OpenAI team's ai_api for ticket operations.

    This demonstrates integration with the OpenAI team's repository:
    https://github.com/natashagit/oss-nml/tree/hw_3_working
    """

    def __init__(
        self,
        ticket_service: TicketServiceAPI,
        user_id: str,
        project_key: str | None = None,
    ) -> None:
        """Initialize adapter with OpenAI team's AI interface.

        Args:
            ticket_service: Jira ticket service implementation
            user_id: User ID for ticket operations
            project_key: Optional Jira project key

        """
        from ai_api import get_client

        self.ticket_service = ticket_service
        self.user_id = user_id
        self.project_key = project_key
        self.ai_client: OpenAIInterface = get_client()
        self._system_prompt = self._build_system_prompt()
        logger.info("OpenAI team's AI interface initialized successfully")

    def _build_system_prompt(self) -> str:
        """Build system prompt for OpenAI with tool calling instructions."""
        return (
            "You are a ticket management assistant. "
            "Parse user requests and respond with JSON tool calls.\n\n"
            "Available tools:\n"
            "- create_ticket: Create a new ticket\n"
            "  Parameters: title (string), description (string), "
            "priority (low/medium/high)\n\n"
            "- list_tickets: List tickets\n"
            "  Parameters: status (open/in_progress/done), limit (number)\n\n"
            "- get_ticket: Get ticket details\n"
            "  Parameters: ticket_id (string)\n\n"
            "Respond ONLY with JSON in this format:\n"
            "{\n"
            '  "tool": "create_ticket",\n'
            '  "parameters": {\n'
            '    "title": "Bug title",\n'
            '    "description": "Bug description",\n'
            '    "priority": "high"\n'
            "  }\n"
            "}"
        )

    async def process_command(self, prompt: str) -> CommandResult:
        """Process natural language command using OpenAI team's AI service.

        Args:
            prompt: Natural language command from user

        Returns:
            CommandResult with execution status

        """
        try:
            # Call OpenAI team's AI service with tool calling schema
            tool_schema = {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "parameters": {"type": "object"},
                },
                "required": ["tool", "parameters"],
            }

            response = self.ai_client.generate_response(
                user_input=prompt,
                system_prompt=self._system_prompt,
                response_schema=tool_schema,
            )

            # Parse the tool call
            if isinstance(response, dict):
                tool_data = response
            elif isinstance(response, str):
                tool_data = json.loads(response)
            else:
                return CommandResult(
                    success=False,
                    message="Invalid response from AI service",
                    error=f"Expected dict or str, got {type(response).__name__}",
                )

            tool_call = self._parse_tool_call(tool_data)
            if not tool_call:
                return CommandResult(
                    success=True,
                    message=str(response),
                )

            # Execute the tool call
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except Exception:
            logger.exception("Error processing command with OpenAI team's service")
            return CommandResult(
                success=False,
                message="Failed to process command",
                error="An error occurred while processing the command",
            )

    def _parse_tool_call(self, tool_data: dict[str, object]) -> ToolCall | None:
        """Parse tool call from OpenAI's response.

        Args:
            tool_data: Response data from OpenAI containing tool information

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
            return None

        return ToolCall(type=tool_type, parameters=parameters)

    async def _execute_tool_call(self, tool_call: ToolCall) -> Ticket | list[Ticket] | None:
        """Execute a tool call against the ticket service.

        Args:
            tool_call: The tool call to execute

        Returns:
            Ticket or list of Tickets depending on the operation

        Raises:
            ValueError: If tool type is unsupported

        """
        if tool_call.type == ToolCallType.CREATE_TICKET:
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
