# Ticket Service

FastAPI-based HTTP service exposing ticket operations over REST endpoints.

## Features

- Complete CRUD operations for tickets and comments
- OAuth 2.0 authentication flow
- Automatic OpenAPI documentation generation
- Request/response validation with Pydantic

## Components

::: ticket_service.main.app

::: ticket_service.models

## Key Endpoints

### Authentication
- `GET /api/v1/auth/login` - Start OAuth flow
- `GET /api/v1/auth/callback` - Handle OAuth callback
- `POST /api/v1/auth/logout` - Clear tokens

### Tickets
- `POST /api/v1/tickets` - Create ticket
- `GET /api/v1/tickets/{id}` - Get ticket
- `GET /api/v1/tickets` - List tickets (with filters)
- `PATCH /api/v1/tickets/{id}` - Update ticket
- `DELETE /api/v1/tickets/{id}` - Delete ticket

### Comments
- `POST /api/v1/tickets/{id}/comments` - Add comment
- `GET /api/v1/tickets/{id}/comments` - Get comments

### Health
- `GET /health` - Service health check

All ticket/comment endpoints require `X-User-ID` and `X-Project-Key` headers.

## Usage

```python
import httpx

# Start OAuth flow
response = httpx.get("http://localhost:8000/api/v1/auth/login")
# Complete OAuth in browser, get user_id

# Use service
headers = {"X-User-ID": "user-id", "X-Project-Key": "PROJ"}
response = httpx.post(
    "http://localhost:8000/api/v1/tickets",
    json={"title": "Bug", "description": "Issue", "reporter": "user@example.com"},
    headers=headers
)
```

## Documentation

Interactive API documentation available at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- `/api/v1/openapi.json` - OpenAPI specification