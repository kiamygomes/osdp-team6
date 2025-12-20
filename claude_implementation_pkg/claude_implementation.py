"""Concrete implementation of AIInterface using Anthropic's Claude API.

This provides a working implementation of the shared AIInterface
that can be used for testing and demonstration.
"""
# mypy: ignore-errors

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, cast

logger = logging.getLogger(__name__)


class ClaudeAIClient:
    """Concrete implementation using Anthropic's Claude API.

    This class duck-types the AIInterface from ai_chat_api without inheriting from it,
    allowing it to work even when the external package is not available or hasn't
    been modified.
    """

    def __init__(self) -> None:
        """Initialize Claude AI client."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set - using test mode")

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response from Claude AI.

        Args:
            user_input: The text provided by the chat user
            system_prompt: Optional instruction set
            response_schema: Optional JSON schema for structured output

        Returns:
            A string (conversation) or a Dict (structured action data)

        """
        if not self.api_key:
            # Test mode - return mock structured response
            return self._mock_response(user_input, response_schema)

        try:
            # Import anthropic locally to make it optional dependency.
            # This allows the module to work in test mode without requiring
            # the anthropic package to be installed.
            import anthropic  # type: ignore[import-not-found]  # noqa: PLC0415

            client = anthropic.Anthropic(api_key=self.api_key)

            messages = [{"role": "user", "content": user_input}]

            if response_schema:
                # For structured output, request JSON mode
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    system=system_prompt or "You are a helpful assistant.",
                    messages=messages,
                )
                content = response.content[0].text
                # Parse JSON response - returns dict
                return cast("str | dict[str, Any]", json.loads(content))
            # For conversational response
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=system_prompt or "You are a helpful assistant.",
                messages=messages,
            )
            return cast("str", response.content[0].text)

        except ImportError:
            logger.warning("anthropic package not installed - using test mode")
            return self._mock_response(user_input, response_schema)
        except Exception:
            logger.exception("Error calling Claude API")
            return self._mock_response(user_input, response_schema)

    def _mock_response(
        self,
        user_input: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate mock response for testing when API not available.

        Args:
            user_input: The user's input text
            response_schema: Optional schema for structured response

        Returns:
            Mock response matching expected format

        """
        lower_input = user_input.lower()

        if response_schema:
            # Return structured tool call based on input
            if "create" in lower_input and "ticket" in lower_input:
                return {
                    "tool": "create_ticket",
                    "parameters": {
                        "title": self._extract_title(user_input),
                        "description": user_input,
                        "priority": self._extract_priority(user_input),
                    },
                }
            if "list" in lower_input or "show" in lower_input:
                return {
                    "tool": "list_tickets",
                    "parameters": {"status": "open", "limit": 10},
                }
            if "update" in lower_input or "move" in lower_input or "get" in lower_input:
                return {
                    "tool": "get_ticket",
                    "parameters": {
                        "ticket_id": self._extract_ticket_id(user_input),
                    },
                }
            # Generic conversational response - return plain message
            return "I can help you with tickets!"
        # Return conversational response
        return "I'm a test implementation. How can I help you with tickets?"

    def _extract_title(self, text: str) -> str:
        """Extract ticket title from user input.

        Args:
            text: User input text

        Returns:
            Extracted title

        """
        import re

        # Look for patterns like "called X", "titled X", "named X"
        patterns = [
            r"called\s+(.+?)(?:\s+with|\s+for|$)",
            r"titled\s+(.+?)(?:\s+with|\s+for|$)",
            r"named\s+(.+?)(?:\s+with|\s+for|$)",
            r":\s*(.+?)(?:\s+with|\s+for|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Remove priority words from title
                title = re.sub(r"\b(high|low|medium|urgent|critical)\s+(priority\s+)?", "", title, flags=re.IGNORECASE).strip()
                if title:
                    return title

        # Look for "for X" pattern
        match = re.search(r"for\s+(.+?)(?:\s+with|$)", text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"\b(high|low|medium|urgent|critical)\s+(priority\s+)?", "", title, flags=re.IGNORECASE).strip()
            if title:
                return title

        # Fallback: remove command words and take the rest
        title = re.sub(r"^(create|make|add)\s+(a\s+)?(ticket|task|issue)\s+(for\s+|about\s+|to\s+)?", "", text, flags=re.IGNORECASE).strip()
        title = re.sub(r"\b(with|having)\s+(high|low|medium|urgent|critical)\s+priority.*$", "", title, flags=re.IGNORECASE).strip()

        return title[:100] if title else text[:100]

    def _extract_priority(self, text: str) -> str:
        """Extract priority from user input.

        Args:
            text: User input text

        Returns:
            Priority level

        """
        lower = text.lower()
        if "urgent" in lower or "high" in lower or "critical" in lower:
            return "high"
        if "low" in lower:
            return "low"
        return "medium"

    def _extract_ticket_id(self, text: str) -> str:
        """Extract ticket ID from user input.

        Args:
            text: User input text

        Returns:
            Ticket ID or placeholder

        """
        # Look for patterns like DEMO-123, PROJ-456, etc.
        match = re.search(r"([A-Z]+-\d+)", text.upper())
        if match:
            return match.group(1)
        return "DEMO-1"  # Fallback
