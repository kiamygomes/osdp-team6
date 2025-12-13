"""AI Adapter for ticket operations with natural language processing.

Supports multiple AI providers:
- Claude (via claude_service_client)
- OpenAI (via OpenAI SDK)

SECOND SUBMISSION - Team Integration:
- ClaudeTeamAdapter: Uses Claude team's ai_chat_api package
- OpenAITeamAdapter: Uses OpenAI team's ai_api package
"""

from ticket_ai_adapter.adapter import AITicketAdapter
from ticket_ai_adapter.models import CommandResult, ToolCall, ToolCallType
from ticket_ai_adapter.openai_adapter import OpenAITicketAdapter
from ticket_ai_adapter.team_integration import ClaudeTeamAdapter, OpenAITeamAdapter

__all__ = [
    "AITicketAdapter",
    "ClaudeTeamAdapter",
    "CommandResult",
    "OpenAITeamAdapter",
    "OpenAITicketAdapter",
    "ToolCall",
    "ToolCallType",
]
