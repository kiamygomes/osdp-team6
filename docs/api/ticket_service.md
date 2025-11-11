# Ticket Service

FastAPI REST service with cookie-based authentication.

## Overview

- **Package**: `ticket_service`
- **Purpose**: HTTP wrapper around `ticket_impl`
- **Dependencies**: fastapi, uvicorn, pydantic
- **Coverage**: 90%+ (25+ tests)

## Key Features

- 13 REST endpoints
- Cookie-based sessions
- OAuth 2.0 integration
- OpenAPI/Swagger docs
- Pydantic validation

## Endpoints

### Authentication
- `GET /api/v1/auth/login` - Start OAuth
- `GET /api/v1/auth/callback` - OAuth callback
- `GET /api/v1/auth/status` - Check status
- `POST /api/v1/auth/logout` - Logout

### Tickets
- `POST /api/v1/tickets` - Create
- `GET /api/v1/tickets/{id}` - Get
- `GET /api/v1/tickets` - List
- `PATCH /api/v1/tickets/{id}` - Update
- `DELETE /api/v1/tickets/{id}` - Delete

### Comments
- `POST /api/v1/tickets/{id}/comments` - Add
- `GET /api/v1/tickets/{id}/comments` - Get

### Health
- `GET /health` - Health check

## Running

```bash
uv run uvicorn ticket_service.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## Authentication

Cookie-based sessions:
1. Visit `/api/v1/auth/login`
2. Complete OAuth flow
3. Cookie set automatically
4. All requests authenticated

For programmatic access, use headers:
- `X-User-ID: user-123`
- `X-Project-Key: PROJ`

## Error Codes

- `200/201` - Success
- `400` - Invalid input
- `401` - Not authenticated
- `404` - Not found
- `500` - Server error

## Configuration

```bash
OAUTH_CLIENT_ID="..."
OAUTH_CLIENT_SECRET="..."
OAUTH_REDIRECT_URI="http://localhost:8000/api/v1/auth/callback"
JIRA_CLOUD_ID="..."
CORS_ORIGINS="http://localhost:3000"
```

## Related

- [ticket_impl](ticket_impl.md) - Backend implementation
- [ticket_client_adapter](ticket_client_adapter.md) - HTTP client
