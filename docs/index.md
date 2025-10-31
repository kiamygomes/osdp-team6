# OSDP Jira Service

A professional-grade microservice for ticketing system integration using component-based architecture with OAuth 2.0 authentication.

## Overview

The OSDP Jira Service provides a flexible platform for integrating with Jira Cloud through a unified interface. The system demonstrates modern Python development practices through clean abstractions, dependency injection, and comprehensive testing.

## Key Features

- **Component-Based Architecture**: Five distinct components with clear responsibilities
- **OAuth 2.0 Integration**: Secure authentication for Jira Cloud
- **Abstract Interface Design**: Clean separation between interface and implementation
- **Type Safety**: Full type hints and Pydantic validation
- **Auto-Generated Clients**: Type-safe HTTP clients from OpenAPI specifications

## Architecture

```
Client Applications
        ↓ HTTP/REST
   ticket_service (FastAPI)
        ↓ TicketServiceAPI
    ticket_impl (Jira)
        ↓ Jira REST API
   External Services
```

**Components:**
- **[ticket_api](api/ticket_api.md)** - Abstract interfaces and data models
- **[ticket_impl](api/ticket_impl.md)** - Jira Cloud integration
- **[ticket_service](api/ticket_service.md)** - FastAPI HTTP service
- **[ticket_client_generated](api/ticket_client_generated.md)** - Auto-generated HTTP client
- **[ticket_client_adapter](api/ticket_client_adapter.md)** - Domain interface adapter

## Quick Start

```bash
# Install dependencies
uv sync --all-packages --extra dev

# Configure OAuth (see .env.example)
export OAUTH_CLIENT_ID="your-jira-oauth-client-id"
export OAUTH_CLIENT_SECRET="your-jira-oauth-client-secret"

# Start the service
uv run uvicorn ticket_service.main:app --reload

# Run tests
uv run pytest
```

## Usage Example

```python
from ticket_client_adapter import RemoteTicketService
from ticket_api import TicketPriority

async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="your-user-id",
    project_key="PROJ"
) as service:
    ticket = await service.create_ticket(
        title="Bug Report",
        description="Found an issue",
        reporter="user@example.com",
        priority=TicketPriority.HIGH
    )
```

## Documentation

- **[Architecture](architecture.md)** - System design and component relationships
- **[Testing](testing.md)** - Testing strategy and guidelines  
- **[CI/CD Setup](circleci-setup.md)** - Continuous integration configuration

### API Reference
- **[Ticket API](api/ticket_api.md)** - Core abstractions and models
- **[Ticket Implementation](api/ticket_impl.md)** - Jira integration
- **[Ticket Service](api/ticket_service.md)** - HTTP service endpoints
- **[Ticket Client Generated](api/ticket_client_generated.md)** - Auto-generated client
- **[Ticket Client Adapter](api/ticket_client_adapter.md)** - Domain interface adapter
