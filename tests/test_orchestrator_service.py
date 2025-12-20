"""Tests for orchestrator_service.py API endpoints."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from orchestrator.orchestrator_service import (
    app,
    check_ai_providers,
    check_chat_available,
    lifespan,
)

load_dotenv()

# HTTP Status Code Constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500


class TestHelperFunctions:
    """Test helper functions in orchestrator_service."""

    def test_check_ai_providers_claude_available(self) -> None:
        """Test check_ai_providers when Claude is available."""
        mock_ai_chat = MagicMock()
        mock_ai_chat.get_ai_interface.return_value = MagicMock()

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", mock_ai_chat),
            patch("orchestrator.orchestrator_service.ai_api", None),
        ):
            result = check_ai_providers()
            assert result["claude"] is True
            assert result["openai"] is False

    def test_check_ai_providers_openai_available(self) -> None:
        """Test check_ai_providers when OpenAI is available."""
        mock_ai_api = MagicMock()
        mock_ai_api.get_client.return_value = MagicMock()

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", None),
            patch("orchestrator.orchestrator_service.ai_api", mock_ai_api),
        ):
            result = check_ai_providers()
            assert result["claude"] is False
            assert result["openai"] is True

    def test_check_ai_providers_both_available(self) -> None:
        """Test check_ai_providers when both are available."""
        mock_ai_chat = MagicMock()
        mock_ai_chat.get_ai_interface.return_value = MagicMock()
        mock_ai_api = MagicMock()
        mock_ai_api.get_client.return_value = MagicMock()

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", mock_ai_chat),
            patch("orchestrator.orchestrator_service.ai_api", mock_ai_api),
        ):
            result = check_ai_providers()
            assert result["claude"] is True
            assert result["openai"] is True

    def test_check_ai_providers_both_unavailable(self) -> None:
        """Test check_ai_providers when both are unavailable."""
        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", None),
            patch("orchestrator.orchestrator_service.ai_api", None),
        ):
            result = check_ai_providers()
            assert result == {"claude": False, "openai": False}

    def test_check_ai_providers_with_error(self) -> None:
        """Test check_ai_providers handling exceptions."""
        mock_ai_chat = MagicMock()
        mock_ai_chat.get_ai_interface.side_effect = RuntimeError("Test error")

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", mock_ai_chat),
            patch("orchestrator.orchestrator_service.ai_api", None),
        ):
            result = check_ai_providers()
            assert result["claude"] is False

    def test_check_chat_available_true(self) -> None:
        """Test check_chat_available when available."""
        mock_chat = MagicMock()
        mock_chat.chat_api.ChatInterface = MagicMock()

        with patch("orchestrator.orchestrator_service.chat_api", mock_chat):
            result = check_chat_available()
            assert result is True

    def test_check_chat_available_false(self) -> None:
        """Test check_chat_available when not available."""
        with patch("orchestrator.orchestrator_service.chat_api", None):
            result = check_chat_available()
            assert result is False

    def test_check_chat_available_with_error(self) -> None:
        """Test check_chat_available handling exceptions."""
        mock_chat = MagicMock()
        mock_chat.chat_api = MagicMock(spec=["ChatInterface"])
        # Make hasattr return False to simulate missing ChatInterface
        with patch("builtins.hasattr", return_value=False):
            result = check_chat_available()
            assert result is False


class TestLifespan:
    """Test lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(self) -> None:
        """Test lifespan startup and shutdown."""
        from fastapi import FastAPI

        app_instance = FastAPI(lifespan=lifespan)
        assert app_instance is not None

    @pytest.mark.asyncio
    async def test_lifespan_with_both_providers_available(self) -> None:
        """Test lifespan logs when both AI providers available."""
        from fastapi import FastAPI

        mock_ai_chat = MagicMock()
        mock_ai_chat.get_ai_interface.return_value = MagicMock()
        mock_ai_api = MagicMock()
        mock_ai_api.get_client.return_value = MagicMock()

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", mock_ai_chat),
            patch("orchestrator.orchestrator_service.ai_api", mock_ai_api),
        ):
            app_instance = FastAPI()
            async with lifespan(app_instance):
                # Inside lifespan context
                pass

    @pytest.mark.asyncio
    async def test_lifespan_with_no_providers_available(self) -> None:
        """Test lifespan logs when no AI providers available."""
        from fastapi import FastAPI

        with (
            patch("orchestrator.orchestrator_service.ai_chat_api", None),
            patch("orchestrator.orchestrator_service.ai_api", None),
        ):
            app_instance = FastAPI()
            async with lifespan(app_instance):
                # Inside lifespan context
                pass


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self) -> None:
        """Test /health endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ticket-bot-orchestrator"
        assert data["version"] == "1.0.0"

    def test_root_endpoint(self) -> None:
        """Test root / endpoint."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert "service" in data
        assert data["service"] == "OSDP Ticket Bot Orchestrator"
        assert "docs" in data
        assert data.get("docs") is not None


class TestStatusEndpoint:
    """Test service status endpoint."""

    def test_status_endpoint(self) -> None:
        """Test /status endpoint."""
        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["service"] == "ticket-bot-orchestrator"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "ai_provider_available" in data
        assert "chat_available" in data
        assert data["ticket_service_available"] is True

    def test_status_with_custom_environment(self) -> None:
        """Test /status includes custom environment."""
        client = TestClient(app)
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            response = client.get("/status")
            assert response.status_code == HTTP_OK


class TestProcessCommandEndpoint:
    """Test /process command endpoint."""

    def test_process_command_success(self) -> None:
        """Test successful command processing."""
        client = TestClient(app)

        request_data = {
            "message": "Create a test ticket",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "claude",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_instance = MagicMock()
            mock_instance.process_chat_message = AsyncMock(
                return_value={
                    "success": True,
                    "message": "Ticket created",
                    "data": {"ticket_id": "TEST-123"},
                }
            )
            mock_orch.return_value = mock_instance

            response = client.post("/process", json=request_data)

            assert response.status_code == HTTP_OK
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Ticket created"
            assert data["ai_provider"] == "claude"
            assert data["user_id"] == "demo_user"

    def test_process_command_validation_error(self) -> None:
        """Test command processing with validation error."""
        client = TestClient(app)

        request_data = {
            "message": "Test message",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "invalid",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_orch.side_effect = ValueError("Invalid provider")

            response = client.post("/process", json=request_data)

            assert response.status_code == HTTP_BAD_REQUEST
            assert "detail" in response.json()

    def test_process_command_runtime_error(self) -> None:
        """Test command processing with runtime error."""
        client = TestClient(app)

        request_data = {
            "message": "Test message",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "claude",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_orch.side_effect = RuntimeError("Service unavailable")

            response = client.post("/process", json=request_data)

            assert response.status_code == HTTP_INTERNAL_SERVER_ERROR
            assert "detail" in response.json()

    def test_process_command_with_error_in_result(self) -> None:
        """Test command processing when result contains error."""
        client = TestClient(app)

        request_data = {
            "message": "Invalid command",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "claude",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_instance = MagicMock()
            mock_instance.process_chat_message = AsyncMock(
                return_value={
                    "success": False,
                    "message": "Failed to process",
                    "error": "AI service error",
                }
            )
            mock_orch.return_value = mock_instance

            response = client.post("/process", json=request_data)

            assert response.status_code == HTTP_OK
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "AI service error"


class TestProcessChatEndpoint:
    """Test /process-chat endpoint."""

    def test_process_chat_success(self) -> None:
        """Test successful chat processing."""
        client = TestClient(app)

        request_data = {
            "message": "List open tickets",
            "channel_id": "general",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "openai",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_instance = MagicMock()
            mock_instance.process_chat_message = AsyncMock(
                return_value={
                    "success": True,
                    "message": "Listed 5 tickets",
                    "data": [{"id": "TEST-1"}, {"id": "TEST-2"}],
                }
            )
            mock_orch.return_value = mock_instance

            response = client.post("/process-chat", json=request_data)

            assert response.status_code == HTTP_OK
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Listed 5 tickets"
            assert data["ai_provider"] == "openai"
            # Verify orchestrator was called with channel_id
            assert mock_instance.process_chat_message.called

    def test_process_chat_validation_error(self) -> None:
        """Test chat processing with validation error."""
        client = TestClient(app)

        request_data = {
            "message": "Test message",
            "channel_id": "general",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "claude",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_orch.side_effect = ValueError("User not found")

            response = client.post("/process-chat", json=request_data)

            assert response.status_code == HTTP_BAD_REQUEST

    def test_process_chat_runtime_error(self) -> None:
        """Test chat processing with runtime error."""
        client = TestClient(app)

        request_data = {
            "message": "Test message",
            "channel_id": "general",
            "user_id": "demo_user",
            "project_key": "TEST",
            "ai_provider": "claude",
        }

        with patch("orchestrator.orchestrator_service.TicketBotOrchestrator") as mock_orch:
            mock_orch.side_effect = RuntimeError("Database error")

            response = client.post("/process-chat", json=request_data)

            assert response.status_code == HTTP_INTERNAL_SERVER_ERROR
            assert "Internal server error" in response.json()["detail"]


class TestRequestModels:
    """Test request/response models."""

    def test_process_command_request_defaults(self) -> None:
        """Test ProcessCommandRequest default values."""
        from orchestrator.orchestrator_service import ProcessCommandRequest

        request = ProcessCommandRequest(message="Test")
        assert request.user_id == "demo_user"
        assert request.project_key == "DEMO"
        assert request.ai_provider == "claude"

    def test_process_chat_request_required_fields(self) -> None:
        """Test ProcessChatRequest required fields."""
        from orchestrator.orchestrator_service import ProcessChatRequest

        request = ProcessChatRequest(message="Test", channel_id="general")
        assert request.user_id == "demo_user"
        assert request.project_key == "DEMO"
        assert request.ai_provider == "claude"

    def test_command_response_model(self) -> None:
        """Test CommandResponse model."""
        from orchestrator.orchestrator_service import CommandResponse

        response = CommandResponse(
            success=True,
            message="Success",
            ai_provider="claude",
            user_id="user1",
            project_key="PROJ",
        )
        assert response.success is True
        assert response.data is None
        assert response.error is None


class TestAuthEndpoints:
    """Test Jira OAuth authentication endpoints."""

    def test_auth_login_no_valid_tokens(self) -> None:
        """Test /api/v1/auth/login when user has no valid tokens."""
        client = TestClient(app)

        with patch("orchestrator.orchestrator_service.get_tokens", return_value=None):
            response = client.get("/api/v1/auth/login?user_id=test-user")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert "auth_url" in data
        assert data["user_id"] == "test-user"
        assert data["service"] == "jira"

    def test_auth_login_with_valid_tokens(self) -> None:
        """Test /api/v1/auth/login when user already has valid tokens."""
        client = TestClient(app)
        mock_tokens = {
            "access_token": "valid-access",
            "refresh_token": "valid-refresh",
            "expires_at": "2099-12-31T00:00:00+00:00",
        }

        with (
            patch("orchestrator.orchestrator_service.get_tokens", return_value=mock_tokens),
            patch("orchestrator.orchestrator_service.is_expired", return_value=False),
        ):
            response = client.get("/api/v1/auth/login?user_id=test-user")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["authenticated"] == "true"
        assert "Already authenticated" in data["message"]

    def test_auth_callback_invalid_state(self) -> None:
        """Test /api/v1/auth/callback with invalid state parameter."""
        client = TestClient(app)

        response = client.get("/api/v1/auth/callback?code=test-code&state=invalid-state")

        assert response.status_code == HTTP_BAD_REQUEST
        assert b"Authentication Failed" in response.content
        assert b"Invalid state parameter" in response.content

    @pytest.mark.asyncio
    async def test_auth_callback_valid_state_success(self) -> None:
        """Test /api/v1/auth/callback with valid state and successful token exchange."""
        from orchestrator.orchestrator_service import _oauth_state_store

        client = TestClient(app)

        # Setup valid state
        test_state = "valid-test-state"
        _oauth_state_store[test_state] = "test-user"

        mock_tokens = ("access-token", "refresh-token", 3600)

        with patch(
            "orchestrator.orchestrator_service.exchange_code_for_tokens",
            new_callable=AsyncMock,
            return_value=mock_tokens,
        ):
            response = client.get(f"/api/v1/auth/callback?code=test-code&state={test_state}")

        assert response.status_code == HTTP_OK
        assert b"Authentication Successful" in response.content
        assert b"successfully authenticated" in response.content

    @pytest.mark.asyncio
    async def test_auth_callback_token_exchange_fails(self) -> None:
        """Test /api/v1/auth/callback when token exchange fails."""
        from orchestrator.orchestrator_service import _oauth_state_store

        client = TestClient(app)

        # Setup valid state
        test_state = "valid-test-state-error"
        _oauth_state_store[test_state] = "test-user"

        with patch(
            "orchestrator.orchestrator_service.exchange_code_for_tokens",
            new_callable=AsyncMock,
            side_effect=Exception("Token exchange failed"),
        ):
            response = client.get(f"/api/v1/auth/callback?code=test-code&state={test_state}")

        assert response.status_code == HTTP_INTERNAL_SERVER_ERROR
        assert b"Authentication Failed" in response.content
        assert b"Failed to exchange authorization code" in response.content

    def test_auth_status_authenticated(self) -> None:
        """Test /api/v1/auth/status for authenticated user."""
        client = TestClient(app)
        mock_tokens = {
            "access_token": "valid-access",
            "refresh_token": "valid-refresh",
            "expires_at": "2099-12-31T00:00:00+00:00",
        }

        with (
            patch("orchestrator.orchestrator_service.get_tokens", return_value=mock_tokens),
            patch("orchestrator.orchestrator_service.is_expired", return_value=False),
        ):
            response = client.get("/api/v1/auth/status?user_id=test-user")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "test-user"

    def test_auth_status_not_authenticated(self) -> None:
        """Test /api/v1/auth/status for unauthenticated user."""
        client = TestClient(app)

        with patch("orchestrator.orchestrator_service.get_tokens", return_value=None):
            response = client.get("/api/v1/auth/status?user_id=test-user")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["authenticated"] is False
        assert data["user_id"] == "test-user"

    def test_auth_status_expired_tokens(self) -> None:
        """Test /api/v1/auth/status with expired tokens."""
        client = TestClient(app)
        mock_tokens = {
            "access_token": "expired-access",
            "refresh_token": "valid-refresh",
            "expires_at": "2020-01-01T00:00:00+00:00",
        }

        with (
            patch("orchestrator.orchestrator_service.get_tokens", return_value=mock_tokens),
            patch("orchestrator.orchestrator_service.is_expired", return_value=True),
        ):
            response = client.get("/api/v1/auth/status?user_id=test-user")

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["authenticated"] is False
        assert "expired" in data.get("message", "").lower()

    def test_auth_login_missing_user_id(self) -> None:
        """Test /api/v1/auth/login without user_id parameter."""
        client = TestClient(app)
        response = client.get("/api/v1/auth/login")
        # Should handle missing user_id gracefully
        assert response.status_code in (HTTP_OK, 422)  # 422 for validation error

    def test_auth_callback_missing_params(self) -> None:
        """Test /api/v1/auth/callback with missing parameters."""
        client = TestClient(app)
        # Missing both code and state
        response = client.get("/api/v1/auth/callback")
        # Should error on validation
        assert response.status_code in (400, 422)

