# /Users/Mikiyas/Desktop/Open_Source/osdp-team6/src/ai_adapter/src/ai_adapter/adapter.py
"""Core AI adapter implementation for ticket operations."""

import json
import logging
from typing import Any
from uuid import UUID

from ticket_api import (
    Comment,
    ServiceError,
    Ticket,
    TicketPriority,
    TicketServiceAPI,
    TicketStatus,
)

from .models import CommandResult, ToolCall, ToolCallType

logger = logging.getLogger(__name__)


class AITicketAdapter:
    """Adapter that integrates AI services with ticket operations.

    This class processes natural language commands, sends them to an AI service
    (Claude), parses the AI response for structured tool calls, and executes
    the corresponding ticket operations.
    """

    def __init__(
        self,
        ticket_service: TicketServiceAPI,
        claude_client: Any,
        user_id: str,
        project_key: str | None = None,
    ) -> None:
        """Initialize the AI ticket adapter.

        Args:
            ticket_service: Implementation of TicketServiceAPI to execute operations
            claude_client: Claude service client for natural language processing
            user_id: User identifier for ticket operations
            project_key: Optional Jira project key for ticket creation

        """
        self.ticket_service = ticket_service
        self.claude_client = claude_client
        self.user_id = user_id
        self.project_key = project_key
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines available tools."""
        return """You are a helpful assistant that helps users manage their tickets.

You have access to the following tools for ticket management:

1. create_ticket: Create a new ticket
   - Parameters: title (required), description (required), priority (optional: low/medium/high/critical), assignee (optional)
   - Example: {"tool": "create_ticket", "parameters": {"title": "Fix login bug", "description": "Users cannot log in", "priority": "high"}}

2. get_ticket: Retrieve a specific ticket
   - Parameters: ticket_id (required)
   - Example: {"tool": "get_ticket", "parameters": {"ticket_id": "uuid-string"}}

3. list_tickets: List tickets with optional filters
   - Parameters: status (optional), assignee (optional), limit (optional)
   - Example: {"tool": "list_tickets", "parameters": {"status": "open", "limit": 10}}

4. update_ticket: Update an existing ticket
   - Parameters: ticket_id (required), title (optional), description (optional), status (optional), priority (optional), assignee (optional)
   - Example: {"tool": "update_ticket", "parameters": {"ticket_id": "uuid", "status": "in_progress"}}

5. add_comment: Add a comment to a ticket
   - Parameters: ticket_id (required), content (required)
   - Example: {"tool": "add_comment", "parameters": {"ticket_id": "uuid", "content": "Working on this issue"}}

6. transition_status: Change ticket status
   - Parameters: ticket_id (required), new_status (required: open/in_progress/resolved/closed)
   - Example: {"tool": "transition_status", "parameters": {"ticket_id": "uuid", "new_status": "resolved"}}

When a user requests a ticket operation, analyze their intent and respond with a JSON object containing the tool call.
Your response should be ONLY the JSON object, nothing else.

If the user's request is unclear or missing required information, ask for clarification instead of making a tool call."""

    async def process_command(self, prompt: str) -> CommandResult:
        """Process a natural language command and execute the corresponding operation.

        This is the main entry point for the adapter. It:
        1. Sends the prompt to Claude with the system prompt
        2. Parses the response for tool calls
        3. Executes the tool call against the ticket service
        4. Returns a structured result

        Args:
            prompt: Natural language command from the user

        Returns:
            CommandResult with execution status and details

        """
        try:
            # Import here to avoid circular dependencies
            from fast_api_client.api.chat import send_chat_message_chat_post
            from fast_api_client.models.chat_request import ChatRequest
            from fast_api_client.models.chat_response import ChatResponse
            from fast_api_client.models.http_validation_error import HTTPValidationError

            # Create the full prompt with system context
            full_prompt = f"{self._system_prompt}\n\nUser request: {prompt}"

            # Send to Claude service
            chat_request = ChatRequest(prompt=full_prompt)
            response = await send_chat_message_chat_post.asyncio(
                client=self.claude_client,
                body=chat_request,
            )

            if not response or isinstance(response, HTTPValidationError):
                return CommandResult(
                    success=False,
                    message="Failed to get response from AI service",
                    error="No response from Claude service",
                )

            # Parse the tool call from response
            tool_call = self._parse_tool_call(response)

            if not tool_call:
                # No tool call means Claude is asking for clarification or providing info
                return CommandResult(
                    success=True,
                    message=response.content,
                )

            # Execute the tool call
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except ServiceError as e:
            logger.exception(f"Service error processing command: {e}")
            return CommandResult(
                success=False,
                message="Failed to execute ticket operation",
                error=str(e),
            )
        except Exception as e:
            logger.exception(f"Unexpected error processing command: {e}")
            return CommandResult(
                success=False,
                message="An unexpected error occurred",
                error=str(e),
            )

    def _parse_tool_call(self, response: Any) -> ToolCall | None:
        """Parse a tool call from the AI response.

        Args:
            response: ChatResponse from Claude service

        Returns:
            Parsed ToolCall or None if no valid tool call found

        """
        content = response.content if hasattr(response, "content") else str(response)

        # First, try to parse the entire content as JSON
        try:
            tool_data = json.loads(content)
            if isinstance(tool_data, dict) and "tool" in tool_data:
                tool_type_str = tool_data.get("tool")
                parameters = tool_data.get("parameters", {})

                # Map tool name to ToolCallType
                try:
                    tool_type = ToolCallType(tool_type_str)
                except ValueError:
                    logger.warning(f"Unknown tool type: {tool_type_str}")
                    return None

                return ToolCall(type=tool_type, parameters=parameters)
        except json.JSONDecodeError:
            pass

        # If that fails, try to extract JSON with balanced braces
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(content):
            if char == "{":
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete JSON object
                    try:
                        potential_json = content[start_idx : i + 1]
                        tool_data = json.loads(potential_json)

                        if isinstance(tool_data, dict) and "tool" in tool_data:
                            tool_type_str = tool_data.get("tool")
                            parameters = tool_data.get("parameters", {})

                            try:
                                tool_type = ToolCallType(tool_type_str)
                            except ValueError:
                                logger.warning(f"Unknown tool type: {tool_type_str}")
                                return None

                            return ToolCall(type=tool_type, parameters=parameters)
                    except json.JSONDecodeError:
                        continue

        return None

    async def _execute_tool_call(self, tool_call: ToolCall) -> Any:
        """Execute a parsed tool call against the ticket service.

        Args:
            tool_call: The parsed tool call to execute

        Returns:
            Result data from the operation (Ticket, Comment, list, etc.)

        Raises:
            ServiceError: If the operation fails

        """
        params = tool_call.parameters

        if tool_call.type == ToolCallType.CREATE_TICKET:
            return await self.ticket_service.create_ticket(
                title=params["title"],
                description=params["description"],
                reporter=self.user_id,
                priority=TicketPriority(params.get("priority", "medium")),
                assignee=params.get("assignee"),
            )

        if tool_call.type == ToolCallType.GET_TICKET:
            ticket_id = UUID(params["ticket_id"])
            return await self.ticket_service.get_ticket(ticket_id)

        if tool_call.type == ToolCallType.LIST_TICKETS:
            status = TicketStatus(params["status"]) if "status" in params else None
            return await self.ticket_service.list_tickets(
                status=status,
                assignee=params.get("assignee"),
                limit=params.get("limit", 100),
            )

        if tool_call.type == ToolCallType.UPDATE_TICKET:
            ticket_id = UUID(params["ticket_id"])
            return await self.ticket_service.update_ticket(
                ticket_id=ticket_id,
                title=params.get("title"),
                description=params.get("description"),
                status=TicketStatus(params["status"]) if "status" in params else None,
                priority=TicketPriority(params["priority"]) if "priority" in params else None,
                assignee=params.get("assignee"),
            )

        if tool_call.type == ToolCallType.ADD_COMMENT:
            ticket_id = UUID(params["ticket_id"])
            return await self.ticket_service.add_comment(
                ticket_id=ticket_id,
                author=self.user_id,
                content=params["content"],
            )

        if tool_call.type == ToolCallType.UPDATE_STATUS:
            ticket_id = UUID(params["ticket_id"])
            return await self.ticket_service.transition_status(
                ticket_id=ticket_id,
                new_status=TicketStatus(params["new_status"]),
            )

        if tool_call.type == ToolCallType.REASSIGN_TICKET:
            ticket_id = UUID(params["ticket_id"])
            return await self.ticket_service.reassign_ticket(
                ticket_id=ticket_id,
                new_assignee=params["new_assignee"],
            )

        msg = f"Unsupported tool call type: {tool_call.type}"
        raise ValueError(msg)

    def _format_success_message(self, tool_type: ToolCallType, result: Any) -> str:
        """Format a user-friendly success message based on the operation and result.

        Args:
            tool_type: The type of operation that was performed
            result: The result data from the operation

        Returns:
            Human-readable success message

        """
        if tool_type == ToolCallType.CREATE_TICKET and isinstance(result, Ticket):
            return f"Successfully created ticket: {result.title} (ID: {result.id})"

        if tool_type == ToolCallType.GET_TICKET and isinstance(result, Ticket):
            return f"Found ticket: {result.title} - Status: {result.status.value}"

        if tool_type == ToolCallType.LIST_TICKETS and isinstance(result, list):
            return f"Found {len(result)} ticket(s)"

        if tool_type == ToolCallType.UPDATE_TICKET and isinstance(result, Ticket):
            return f"Successfully updated ticket: {result.title}"

        if tool_type == ToolCallType.ADD_COMMENT and isinstance(result, Comment):
            return "Successfully added comment to ticket"

        if tool_type in (ToolCallType.UPDATE_STATUS, ToolCallType.REASSIGN_TICKET) and isinstance(
            result, Ticket
        ):
            return f"Successfully updated ticket: {result.title}"

        return "Operation completed successfully"
