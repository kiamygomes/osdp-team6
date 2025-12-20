"""Integration adapters that use other teams' AI service packages.

This module demonstrates the Second Submission requirement:
- Integration with Claude team's AI service (via ai_chat_adapter)
- Integration with OpenAI team's AI service (via ai_adapter)
- Both integrated with our Jira Ticket Service

Both adapters now inherit from BaseTicketAIAdapter to reduce duplication
and maintain consistent behavior.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base_adapter import BaseTicketAIAdapter
from .models import CommandResult

if TYPE_CHECKING:
    from ai_api import AIInterface as OpenAIInterface
    from ai_chat_api import AIInterface as ClaudeInterface
    from ticket_api import TicketServiceAPI

logger = logging.getLogger(__name__)


class ClaudeTeamAdapter(BaseTicketAIAdapter):
    """Adapter using Claude team's ai_chat_api for ticket operations.

    This demonstrates integration with the Claude team's repository:
    https://github.com/shichenz1999/oss-taapp/tree/hw3

    Inherits common functionality from BaseTicketAIAdapter to reduce duplication.
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

        super().__init__(ticket_service, user_id, project_key)
        self.ai_client: ClaudeInterface = get_ai_interface()
        self._system_prompt = self._build_system_prompt()
        logger.info("Claude team's AI interface initialized successfully")

    async def process_command(self, prompt: str) -> CommandResult:
        """Process natural language command using Claude team's AI service.

        Args:
            prompt: Natural language command from user

        Returns:
            CommandResult with execution status

        """
        logger.info("🔍 Processing command with Claude AI: %s", prompt)
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

            logger.info(
                "🔍 Calling Claude AI with system prompt length: %d",
                len(self._system_prompt),
            )
            response = self.ai_client.generate_response(
                user_input=prompt,
                system_prompt=self._system_prompt,
                response_schema=tool_schema,
            )

            # Log the raw AI response for debugging
            logger.info("🔍 Claude AI raw response: %s", response)
            logger.info("🔍 Response type: %s", type(response).__name__)

            # Parse response to dictionary using base class method
            tool_data = self._parse_response_to_dict(response)
            logger.info("🔍 Parsed tool_data: %s", tool_data)
            if not tool_data:
                return CommandResult(
                    success=False,
                    message="Invalid response from AI service",
                    error=f"Expected dict or JSON string, got {type(response).__name__}",
                )

            # Parse tool call using base class method
            tool_call = self._parse_tool_call_from_dict(tool_data)
            logger.info("🔍 Parsed tool_call: %s", tool_call)
            if not tool_call:
                return CommandResult(
                    success=True,
                    message=str(response),
                )

            # Execute the tool call (base class method handles validation)
            logger.info(
                "🔍 Executing tool call: %s with params: %s",
                tool_call.type,
                tool_call.parameters,
            )
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except ValueError as e:
            # Parameter validation errors
            logger.warning("Validation error: %s", e)
            return CommandResult(
                success=False,
                message="Invalid parameters in AI response",
                error=str(e),
            )
        except Exception:
            logger.exception("Error processing command with Claude team's service")
            return CommandResult(
                success=False,
                message="Failed to process command",
                error="An error occurred while processing the command",
            )


class OpenAITeamAdapter(BaseTicketAIAdapter):
    """Adapter using OpenAI team's ai_api for ticket operations.

    This demonstrates integration with the OpenAI team's repository:
    https://github.com/natashagit/oss-nml/tree/hw_3_working

    Inherits common functionality from BaseTicketAIAdapter to reduce duplication.
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

        super().__init__(ticket_service, user_id, project_key)
        self.ai_client: OpenAIInterface = get_client()
        self._system_prompt = self._build_system_prompt()
        logger.info("OpenAI team's AI interface initialized successfully")

    async def process_command(self, prompt: str) -> CommandResult:
        """Process natural language command using OpenAI team's AI service.

        Args:
            prompt: Natural language command from user

        Returns:
            CommandResult with execution status

        """
        logger.info("🔍 Processing command with OpenAI: %s", prompt)
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

            logger.info("🔍 Calling OpenAI with system prompt length: %d", len(self._system_prompt))
            response = self.ai_client.generate_response(
                user_input=prompt,
                system_prompt=self._system_prompt,
                response_schema=tool_schema,
            )

            # Log the raw AI response for debugging
            logger.info("🔍 OpenAI raw response: %s", response)
            logger.info("🔍 Response type: %s", type(response).__name__)

            # Parse response to dictionary using base class method
            tool_data = self._parse_response_to_dict(response)
            logger.info("🔍 Parsed tool_data: %s", tool_data)
            if not tool_data:
                return CommandResult(
                    success=False,
                    message="Invalid response from AI service",
                    error=f"Expected dict or JSON string, got {type(response).__name__}",
                )

            # Parse tool call using base class method
            tool_call = self._parse_tool_call_from_dict(tool_data)
            logger.info("🔍 Parsed tool_call: %s", tool_call)
            if not tool_call:
                return CommandResult(
                    success=True,
                    message=str(response),
                )

            # Execute the tool call (base class method handles validation)
            logger.info(
                "🔍 Executing tool call: %s with params: %s",
                tool_call.type,
                tool_call.parameters,
            )
            result_data = await self._execute_tool_call(tool_call)

            return CommandResult(
                success=True,
                message=self._format_success_message(tool_call.type, result_data),
                data=result_data,
            )

        except ValueError as e:
            # Parameter validation errors
            logger.warning("Validation error: %s", e)
            return CommandResult(
                success=False,
                message="Invalid parameters in AI response",
                error=str(e),
            )
        except Exception:
            logger.exception("Error processing command with OpenAI team's service")
            return CommandResult(
                success=False,
                message="Failed to process command",
                error="An error occurred while processing the command",
            )
