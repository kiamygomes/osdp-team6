# Ticket Implementation

Jira Cloud implementation with OAuth 2.0.

## Overview

- **Package**: `ticket_impl`
- **Purpose**: Jira Cloud REST API v3 integration
- **Dependencies**: httpx, sqlalchemy, python-dotenv
- **Coverage**: 95%+ (30+ tests)

## Key Features

- OAuth 2.0 (3-legged) with automatic token refresh
- UUID abstraction (hides Jira issue keys)
- Atlassian Document Format (ADF) support
- SQLAlchemy token and mapping storage
- Comprehensive error handling

## Components

- `impl.py` - Main `TicketImpl` class
- `jira_client.py` - Jira REST API calls
- `oauth.py` - OAuth flow and token management
- `storage.py` - Database models and operations
- `config.py` - Environment configuration

## Configuration

```bash
OAUTH_CLIENT_ID="your-jira-oauth-client-id"
OAUTH_CLIENT_SECRET="your-jira-oauth-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8000/api/v1/auth/callback"
JIRA_CLOUD_ID="your-jira-cloud-id"
DB_URL="sqlite:///./tickets.db"
```

## Usage

```python
from ticket_impl import TicketImpl

service = TicketImpl(user_id="user-123", project_key="PROJ")
ticket = await service.create_ticket(
    title="Bug Report",
    description="Found an issue",
    reporter="user@example.com"
)
```

## OAuth Flow

1. User visits `/api/v1/auth/login`
2. Redirects to Jira
3. User grants permission
4. Callback with authorization code
5. Exchange for access/refresh tokens
6. Store in database
7. Auto-refresh when expired

## UUID Abstraction

Uses UUID v5 (deterministic) to hide Jira keys:
- User sees: `550e8400-e29b-41d4-a716-446655440000`
- Jira sees: `PROJ-123`
- Mapping stored in SQLite/PostgreSQL

## Related

- [ticket_api](ticket_api.md) - Abstract interface
- [ticket_service](ticket_service.md) - HTTP service using this
