"""Tests for Claude AI implementation."""

from __future__ import annotations

import builtins
import os
from typing import Any
from unittest.mock import MagicMock, patch

from claude_implementation_pkg.claude_implementation import ClaudeAIClient  # type: ignore[import-not-found]


class TestClaudeAIClient:
    """Test the Claude AI client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            client = ClaudeAIClient()
            assert client.api_key == "test-key"

    def test_init_without_api_key(self) -> None:
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            client = ClaudeAIClient()
            assert client.api_key is None

    def test_generate_response_mock_create_ticket(self) -> None:
        """Test mock response for create ticket command."""
        client = ClaudeAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response(
            "Create a high priority ticket for fixing login bug", response_schema={"type": "object"}
        )

        assert isinstance(response, dict)
        assert response["tool"] == "create_ticket"
        assert "title" in response["parameters"]
        assert response["parameters"]["priority"] == "high"

    def test_generate_response_mock_list_tickets(self) -> None:
        """Test mock response for list tickets command."""
        client = ClaudeAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Show me all open tickets", response_schema={"type": "object"})

        assert isinstance(response, dict)
        assert response["tool"] == "list_tickets"
        assert response["parameters"]["status"] == "open"

    def test_generate_response_mock_get_ticket(self) -> None:
        """Test mock response for get ticket command."""
        client = ClaudeAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Get ticket DEMO-123", response_schema={"type": "object"})

        assert isinstance(response, dict)
        assert response["tool"] == "get_ticket"
        assert "ticket_id" in response["parameters"]

    def test_generate_response_mock_conversational(self) -> None:
        """Test mock conversational response."""
        client = ClaudeAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Hello, how are you?", response_schema={"type": "object"})

        assert response == "I can help you with tickets!"

    def test_generate_response_mock_no_schema(self) -> None:
        """Test mock response without schema."""
        client = ClaudeAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Hello")

        assert isinstance(response, str)
        assert "test implementation" in response.lower()

    def test_generate_response_with_api_structured(self) -> None:
        """Test API call with structured response."""
        with patch("builtins.__import__") as mock_import:
            # Mock the anthropic module
            mock_anthropic = MagicMock()
            mock_client = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client

            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = '{"tool": "create_ticket", "parameters": {}}'
            mock_client.messages.create.return_value = mock_response

            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "anthropic":
                    return mock_anthropic
                return builtins.__import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            client = ClaudeAIClient()
            client.api_key = "test-key"

            response = client.generate_response(
                "Create a ticket", system_prompt="You are helpful", response_schema={"type": "object"}
            )

            assert isinstance(response, dict)
            assert response["tool"] == "create_ticket"

    def test_generate_response_import_error(self) -> None:
        """Test handling of import error."""
        client = ClaudeAIClient()
        client.api_key = "test-key"

        with patch("builtins.__import__", side_effect=ImportError):
            response = client.generate_response("Create a ticket", response_schema={"type": "object"})

            # Should fall back to mock response
            assert isinstance(response, dict)

    def test_generate_response_api_error(self) -> None:
        """Test handling of API error."""
        with patch("builtins.__import__") as mock_import:
            # Mock the anthropic module to raise an exception
            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "anthropic":
                    error_msg = "API Error"
                    raise ImportError(error_msg)
                return builtins.__import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            client = ClaudeAIClient()
            client.api_key = "test-key"

            response = client.generate_response("Create a ticket", response_schema={"type": "object"})

            # Should fall back to mock response
            assert isinstance(response, dict)

    def test_extract_title_with_colon(self) -> None:
        """Test title extraction with colon separator."""
        client = ClaudeAIClient()

        title = client._extract_title("Create ticket: Fix login bug")
        assert title == "Fix login bug"

    def test_extract_title_fallback(self) -> None:
        """Test title extraction fallback."""
        client = ClaudeAIClient()

        long_text = "x" * 150
        title = client._extract_title(long_text)
        expected_title_length = 100
        assert len(title) == expected_title_length

    def test_extract_priority_high(self) -> None:
        """Test priority extraction for high priority."""
        client = ClaudeAIClient()

        assert client._extract_priority("urgent bug fix") == "high"
        assert client._extract_priority("high priority task") == "high"
        assert client._extract_priority("critical issue") == "high"

    def test_extract_priority_low(self) -> None:
        """Test priority extraction for low priority."""
        client = ClaudeAIClient()

        assert client._extract_priority("low priority enhancement") == "low"

    def test_extract_priority_default(self) -> None:
        """Test priority extraction default."""
        client = ClaudeAIClient()

        assert client._extract_priority("normal task") == "medium"

    def test_extract_ticket_id_found(self) -> None:
        """Test ticket ID extraction when found."""
        client = ClaudeAIClient()

        ticket_id = client._extract_ticket_id("Update ticket DEMO-123 status")
        assert ticket_id == "DEMO-123"

    def test_extract_ticket_id_fallback(self) -> None:
        """Test ticket ID extraction fallback."""
        client = ClaudeAIClient()

        ticket_id = client._extract_ticket_id("Update some ticket")
        assert ticket_id == "DEMO-1"
