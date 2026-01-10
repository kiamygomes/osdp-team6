"""Unit tests for AI adapter models."""

from ticket_ai_adapter.models import CommandResult, ToolCall, ToolCallType


class TestToolCallType:
    """Test ToolCallType enum."""

    def test_all_tool_types_exist(self) -> None:
        """Test that all expected tool types are defined."""
        expected_types = [
            "create_ticket",
            "get_ticket",
            "list_tickets",
            "update_ticket",
            "delete_ticket",
            "add_comment",
            "transition_status",
            "reassign_ticket",
        ]
        for tool_type in expected_types:
            assert ToolCallType(tool_type)


class TestToolCall:
    """Test ToolCall model."""

    def test_tool_call_creation(self) -> None:
        """Test creating a ToolCall instance."""
        tool_call = ToolCall(
            type=ToolCallType.CREATE_TICKET,
            parameters={"title": "Test", "description": "Test desc"},
        )
        assert tool_call.type == ToolCallType.CREATE_TICKET
        assert tool_call.parameters["title"] == "Test"

    def test_tool_call_with_empty_parameters(self) -> None:
        """Test ToolCall with empty parameters."""
        tool_call = ToolCall(type=ToolCallType.LIST_TICKETS, parameters={})
        assert tool_call.type == ToolCallType.LIST_TICKETS
        assert tool_call.parameters == {}


class TestCommandResult:
    """Test CommandResult model."""

    def test_successful_result(self) -> None:
        """Test creating a successful CommandResult."""
        result = CommandResult(
            success=True,
            message="Operation completed",
            data={"id": "123"},
        )
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.data == {"id": "123"}
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test creating a failed CommandResult."""
        result = CommandResult(
            success=False,
            message="Operation failed",
            error="Something went wrong",
        )
        assert result.success is False
        assert result.message == "Operation failed"
        assert result.error == "Something went wrong"
        assert result.data is None

    def test_result_without_data(self) -> None:
        """Test CommandResult without data field."""
        result = CommandResult(success=True, message="Done")
        assert result.success is True
        assert result.message == "Done"
        assert result.data is None
        assert result.error is None
