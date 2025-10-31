# Ticket Implementation

Concrete implementation of the `TicketServiceAPI` that integrates with Jira Cloud using OAuth 2.0 authentication.

## Overview

The `ticket_impl` package provides a production-ready implementation that:

- Implements the complete `TicketServiceAPI` interface
- Integrates with Jira Cloud REST API v3
- Handles OAuth 2.0 authentication and token management
- Maps domain UUIDs to Jira issue keys transparently
- Transforms data between domain models and Jira formats
- Provides persistent storage for tokens and mappings

## Core Components

### TicketImpl Service

The main service class implementing `TicketServiceAPI`:

```python
from ticket_impl import TicketImpl

service = TicketImpl(user_id="user-123", project_key="PROJ")
ticket = await service.create_ticket(
    title="Bug Report",
    description="System issue description",
    reporter="user@example.com"
)
```

### OAuth Management

Handles Jira Cloud OAuth 2.0 authentication:

```python
from ticket_impl.oauth import build_authorize_url, exchange_code_for_tokens

# Start OAuth flow
auth_url = build_authorize_url(state="csrf-token")

# Handle callback
await exchange_code_for_tokens(user_id="user-123", code="auth-code")
```

### Jira Client

Low-level HTTP client for Jira REST API operations:
- Issue creation, retrieval, and updates
- Comment management
- User lookup and validation
- Workflow transitions

### Storage Layer

SQLite-based persistence for:
- OAuth access and refresh tokens
- UUID to Jira key mappings
- User session management

## Configuration

Set environment variables for Jira integration:

```bash
JIRA_API_BASE="https://your-domain.atlassian.net"
OAUTH_CLIENT_ID="your-oauth-client-id"
OAUTH_CLIENT_SECRET="your-oauth-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8000/api/v1/auth/callback"
DB_URL="sqlite:///jira_tokens.db"
```

## Testing

The implementation includes comprehensive tests with mocked Jira API responses:

### Test Structure

**test_ticket_impl.py** - End-to-end implementation testing
- Complete CRUD operations with mocked Jira responses
- OAuth token handling and refresh
- Data transformation validation
- Error handling and edge cases
- UUID to Jira key mapping

**conftest.py** - Test configuration and fixtures
- Mock token setup for testing
- Jira API response fixtures
- Test database configuration

### Test Categories

- **CRUD Operations**: Create, read, update, delete tickets
- **Comment Management**: Add and retrieve comments
- **OAuth Flow**: Token exchange and refresh
- **Data Mapping**: UUID to Jira key transformation
- **Error Handling**: Network failures and API errors

### Running Tests

```bash
# All implementation tests
uv run pytest src/ticket_impl/tests/ -v

# Specific test scenarios
uv run pytest src/ticket_impl/tests/test_ticket_impl.py::test_create_get_list_update_comment_delete -v

# Coverage reporting
uv run pytest src/ticket_impl/tests/ --cov=ticket_impl --cov-report=term-missing
```

### Mock Strategy

Tests use `respx` to mock Jira API responses:
- User lookup responses
- Issue creation and retrieval
- Comment operations
- Workflow transitions
- Error scenarios

## Architecture

### Data Flow

```
Domain Models → TicketImpl → Jira Client → Jira REST API
     ↑              ↓            ↓             ↓
UUID Mapping ← Storage Layer ← OAuth Tokens ← Auth Response
```

### Key Features

- **UUID Abstraction**: Clean domain UUIDs mapped to Jira issue keys
- **Token Management**: Automatic refresh of expired OAuth tokens
- **Data Transformation**: Bidirectional conversion between domain and Jira models
- **Error Handling**: Graceful handling of network and API errors
- **Type Safety**: Full type annotations and validation

## Integration

### With Ticket Service

```python
from ticket_impl import TicketImpl
from ticket_service import get_ticket_service

def get_ticket_service() -> TicketServiceAPI:
    return TicketImpl(
        user_id=get_current_user_id(),
        project_key=get_project_key()
    )
```

### With Other Components

The implementation works seamlessly with other components through the `TicketServiceAPI` interface:
- `ticket_service` uses it as the backend implementation
- `ticket_client_adapter` provides the same interface for remote access
- All components share the same domain models from `ticket_api`

## Dependencies

- `ticket_api` - Abstract interface and domain models
- `httpx` - Async HTTP client for Jira API calls
- `sqlalchemy` - Database ORM for token and mapping storage
- `pydantic` - Data validation and serialization