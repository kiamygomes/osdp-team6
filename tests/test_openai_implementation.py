"""Tests for OpenAI implementation."""

from __future__ import annotations

import builtins
import os
from typing import Any
from unittest.mock import patch

from openai_implementation_pkg.openai_implementation import OpenAIClient  # type: ignore[import-not-found]


class TestOpenAIClient:
    """Test the OpenAI client implementation."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = OpenAIClient()
            assert client.api_key == "test-key"

    def test_init_without_api_key(self) -> None:
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            client = OpenAIClient()
            assert client.api_key is None

    def test_generate_response_mock_create_ticket(self) -> None:
        """Test mock response for create ticket command."""
        client = OpenAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response(
            "Create a high priority ticket for fixing login bug", "You are helpful", response_schema={"type": "object"}
        )

        assert isinstance(response, dict)
        assert response["tool"] == "create_ticket"
        assert "title" in response["parameters"]
        assert response["parameters"]["priority"] == "high"

    def test_generate_response_mock_list_tickets(self) -> None:
        """Test mock response for list tickets command."""
        client = OpenAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Show me all open tickets", "You are helpful", response_schema={"type": "object"})

        assert isinstance(response, dict)
        assert response["tool"] == "list_tickets"
        assert response["parameters"]["status"] == "open"

    def test_generate_response_mock_get_ticket(self) -> None:
        """Test mock response for get ticket command."""
        client = OpenAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Get ticket DEMO-123", "You are helpful", response_schema={"type": "object"})

        assert isinstance(response, dict)
        assert response["tool"] == "get_ticket"
        assert "ticket_id" in response["parameters"]

    def test_generate_response_mock_conversational(self) -> None:
        """Test mock conversational response."""
        client = OpenAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Hello, how are you?", "You are helpful", response_schema={"type": "object"})

        assert response == "I can help you with tickets!"

    def test_generate_response_mock_no_schema(self) -> None:
        """Test mock response without schema."""
        client = OpenAIClient()
        client.api_key = None  # Force test mode

        response = client.generate_response("Hello", "You are helpful")

        assert isinstance(response, str)
        assert "test implementation" in response.lower()

    def test_generate_response_import_error(self) -> None:
        """Test handling of import error."""
        client = OpenAIClient()
        client.api_key = "test-key"

        with patch("builtins.__import__", side_effect=ImportError):
            response = client.generate_response("Create a ticket", "You are helpful", response_schema={"type": "object"})

            # Should fall back to mock response
            assert isinstance(response, dict)

    def test_generate_response_api_error(self) -> None:
        """Test handling of API error."""
        with patch("builtins.__import__") as mock_import:
            # Mock the openai module to raise an exception
            def import_side_effect(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "openai":
                    error_msg = "API Error"
                    raise ImportError(error_msg)
                return builtins.__import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            client = OpenAIClient()
            client.api_key = "test-key"

            response = client.generate_response("Create a ticket", "You are helpful", response_schema={"type": "object"})

            # Should fall back to mock response
            assert isinstance(response, dict)

    def test_extract_title_with_colon(self) -> None:
        """Test title extraction with colon separator."""
        client = OpenAIClient()

        title = client._extract_title("Create ticket: Fix login bug")
        assert title == "Fix login bug"

    def test_extract_title_fallback(self) -> None:
        """Test title extraction fallback."""
        client = OpenAIClient()

        long_text = "x" * 150
        title = client._extract_title(long_text)
        expected_title_length = 100
        assert len(title) == expected_title_length

    def test_extract_priority_high(self) -> None:
        """Test priority extraction for high priority."""
        client = OpenAIClient()

        assert client._extract_priority("urgent bug fix") == "high"
        assert client._extract_priority("high priority task") == "high"
        assert client._extract_priority("critical issue") == "high"

    def test_extract_priority_low(self) -> None:
        """Test priority extraction for low priority."""
        client = OpenAIClient()

        assert client._extract_priority("low priority enhancement") == "low"

    def test_extract_priority_default(self) -> None:
        """Test priority extraction default."""
        client = OpenAIClient()

        assert client._extract_priority("normal task") == "medium"

    def test_extract_ticket_id_found(self) -> None:
        """Test ticket ID extraction when found."""
        client = OpenAIClient()

        ticket_id = client._extract_ticket_id("Update ticket DEMO-123 status")
        assert ticket_id == "DEMO-123"

    def test_extract_ticket_id_fallback(self) -> None:
        """Test ticket ID extraction fallback."""
        client = OpenAIClient()

        ticket_id = client._extract_ticket_id("Update some ticket")
        assert ticket_id == "DEMO-1"
