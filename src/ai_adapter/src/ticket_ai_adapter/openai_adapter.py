"""OpenAI-based AI adapter implementation for ticket operations."""

import json
import logging
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


class OpenAITicketAdapter:
    """Adapter that integrates OpenAI services with ticket operations.

    This class processes natural language commands, sends them to OpenAI,
    parses the AI response for structured tool calls, and executes
    the corresponding ticket operations.

    This is the SECOND AI provider, demonstrating multi-provider support.
    """

    def __init__(
        self,
        ticket_service: TicketServiceAPI,
        openai_api_key: str,
        user_id: str,
        model: str = "gpt-4o-mini",
        project_key: str | None = None,
    ) -> None:
        """Initialize the OpenAI ticket adapter.

        Args:
            ticket_service: Implementation of TicketServiceAPI to execute operations
            openai_api_key: OpenAI API key
            user_id: User identifier for ticket operations
            model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
            project_key: Optional Jira project key for ticket creation

        """
        self.ticket_service = ticket_service
        self.user_id = user_id
        self.project_key = project_key
        self.model = model
        self._system_prompt = self._build_system_prompt()

        # Initialize OpenAI client
        try:
            import openai

            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        except ImportError as e:
            msg = "openai package not installed. Run: pip install openai"
            raise ImportError(msg) from e

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines available tools."""
        return """You are a helpful assistant that helps users manage tickets.

You have access to the following tools for ticket management:

1. create_ticket: Create a new ticket
   - Parameters: title (required), description (required),
     priority (optional: low/medium/high/critical), assignee (optional)
   - Example: {"tool": "create_ticket", "parameters":
     {"title": "Fix login bug", "description": "Users cannot log in",
      "priority": "high"}}

2. get_ticket: Retrieve a specific ticket
   - Parameters: ticket_id (required)
   - Example: {"tool": "get_ticket",
     "parameters": {"ticket_id": "uuid-string"}}

3. list_tickets: List tickets with optional filters
   - Parameters: status (optional), assignee (optional), limit (optional)
   - Example: {"tool": "list_tickets",
     "parameters": {"status": "open", "limit": 10}}

4. update_ticket: Update an existing ticket
   - Parameters: ticket_id (required), title (optional),
     description (optional), status (optional), priority (optional),
     assignee (optional)
   - Example: {"tool": "update_ticket",
     "parameters": {"ticket_id": "uuid", "status": "in_progress"}}

5. add_comment: Add a comment to a ticket
   - Parameters: ticket_id (required), content (required)
   - Example: {"tool": "add_comment",
     "parameters": {"ticket_id": "uuid", "content": "Working on this"}}

6. transition_status: Change ticket status
   - Parameters: ticket_id (required),
     new_status (required: open/in_progress/resolved/closed)
   - Example: {"tool": "transition_status",
     "parameters": {"ticket_id": "uuid", "new_status": "resolved"}}

When a user requests a ticket operation, analyze their intent and
respond with ONLY a JSON object containing the tool call.
If the user's request is unclear or missing required information,
ask for clarification instead of making a tool call."""

    async def process_command(self, prompt: str) -> CommandResult:
        """Process a natural language command and execute the corresponding operation.

        This is the main entry point for the adapter. It:
        1. Sends the prompt to OpenAI with the system prompt
        2. Parses the response for tool calls
        3. Executes the tool call against the ticket service
        4. Returns a structured result

        Args:
            prompt: Natural language command from the user

        Returns:
            CommandResult with execution status and details

        """
        try:
            # Send to OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},  # Request JSON response
            )

            if not response.choices or not response.choices[0].message.content:
                return CommandResult(
                    success=False,
                    message="Failed to get response from AI service",
                    error="No response from OpenAI",
                )

            content = response.choices[0].message.content

            # Parse the tool call from response
            tool_call = self._parse_tool_call(content)

            if not tool_call:
                # No tool call means AI is asking for clarification or providing info
                return CommandResult(
                    success=True,
                    message=content,
                )

            # Execute the tool call
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except ServiceError as e:
            logger.exception("Service error processing command")
            return CommandResult(
                success=False,
                message="Failed to execute ticket operation",
                error=str(e),
            )
        except Exception as e:
            logger.exception("Unexpected error processing command")
            return CommandResult(
                success=False,
                message="An unexpected error occurred",
                error=str(e),
            )

    def _parse_tool_call(self, content: str) -> ToolCall | None:
        """Parse a tool call from the AI response.

        Args:
            content: JSON string from OpenAI

        Returns:
            Parsed ToolCall or None if no valid tool call found

        """
        try:
            tool_data = json.loads(content)
            if isinstance(tool_data, dict) and "tool" in tool_data:
                tool_type_str = tool_data.get("tool")
                parameters = tool_data.get("parameters", {})

                # Map tool name to ToolCallType
                try:
                    tool_type = ToolCallType(tool_type_str)
                except ValueError:
                    logger.warning("Unknown tool type: %s", tool_type_str)
                    return None

                return ToolCall(type=tool_type, parameters=parameters)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from OpenAI response: %s", content)
            return None

        return None

    async def _execute_tool_call(
        self, tool_call: ToolCall
    ) -> Ticket | Comment | list[Ticket] | None:
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

        if tool_call.type == ToolCallType.TRANSITION_STATUS:
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

    def _format_success_message(self, tool_type: ToolCallType, result: object) -> str:
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

        update_types = (ToolCallType.TRANSITION_STATUS, ToolCallType.REASSIGN_TICKET)
        if tool_type in update_types and isinstance(result, Ticket):
            return f"Successfully updated ticket: {result.title}"

        return "Operation completed successfully"
