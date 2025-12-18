# AI Interface Implementations

This directory contains concrete implementations of the shared AI interfaces provided by external teams.

## Structure

- `claude/` - Claude AI implementation conforming to the claude_team's AIInterface
- `openai/` - OpenAI implementation conforming to the openai_team's AIInterface

## Why These Are Here

These implementations were created to demonstrate integration with the external teams' shared interfaces. They are kept in our repository because:

1. The external team repositories are submodules we don't have write access to
2. CI/CD needs to access these implementations to build and test
3. They conform to the interfaces defined by the external teams

## Usage

These implementations are automatically used by the adapters in `src/ai_adapter/` when the external team packages are imported. They provide both test mode (without API keys) and production mode (with API keys).

## Integration Points

- `external/claude_team/src/ai_chat_api/src/ai_chat_api/client.py` - References `claude_implementation.py`
- `external/openai_team/src/ai_api/src/ai_api/__init__.py` - References `openai_implementation.py`

These files are symlinked or imported by the external team packages during runtime.
