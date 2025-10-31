# Ticket Implementation

Concrete implementation of `TicketServiceAPI` for Jira Cloud integration.

## Features

- Full Jira Cloud REST API v3 integration
- OAuth 2.0 authentication with token management
- UUID to Jira key mapping for clean abstractions
- Data transformation between domain and Jira models

## Components

::: ticket_impl.impl.TicketImpl

::: ticket_impl.oauth

::: ticket_impl.jira_client

::: ticket_impl.storage

## Usage

```python
from ticket_impl import TicketImpl

# Initialize service
service = TicketImpl(user_id="user-123", project_key="PROJ")

# Create ticket
ticket = await service.create_ticket(
    title="Bug Report",
    description="Issue description",
    reporter="user@example.com"
)

# OAuth flow
from ticket_impl.oauth import build_authorize_url, exchange_code_for_tokens

auth_url = build_authorize_url(state="csrf-token")
await exchange_code_for_tokens(user_id="user-123", code="auth-code")
```

## Configuration

```bash
JIRA_API_BASE="https://your-domain.atlassian.net"
OAUTH_CLIENT_ID="your-oauth-client-id"
OAUTH_CLIENT_SECRET="your-oauth-client-secret"
DB_URL="sqlite:///jira_tokens.db"
```

