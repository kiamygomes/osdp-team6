# Ticket Service

FastAPI-based HTTP service that exposes ticket operations through REST endpoints with OAuth 2.0 authentication.

## Overview

The `ticket_service` package provides a production-ready web service that:

- Exposes the `TicketServiceAPI` through REST endpoints
- Handles OAuth 2.0 authentication flow for Jira integration
- Provides automatic request/response validation
- Generates OpenAPI documentation
- Supports CORS for web applications
- Uses dependency injection for service implementations

## Core Features

### REST API Endpoints

**Authentication**
- `GET /api/v1/auth/login` - Start OAuth flow
- `GET /api/v1/auth/callback` - Handle OAuth callback
- `GET /api/v1/auth/status` - Check authentication status
- `POST /api/v1/auth/logout` - Clear user tokens

**Tickets**
- `POST /api/v1/tickets` - Create new ticket
- `GET /api/v1/tickets/{id}` - Get ticket by ID
- `GET /api/v1/tickets` - List tickets with filters
- `PATCH /api/v1/tickets/{id}` - Update ticket
- `DELETE /api/v1/tickets/{id}` - Delete ticket

**Comments**
- `POST /api/v1/tickets/{id}/comments` - Add comment
- `GET /api/v1/tickets/{id}/comments` - Get ticket comments

**Health**
- `GET /health` - Service health check

### Request/Response Models

Pydantic models for API validation:
- `TicketCreateRequest` / `TicketUpdateRequest`
- `CommentCreateRequest`
- `TicketResponse` / `TicketListResponse`
- `CommentResponse`

## Usage

### Starting the Service

```bash
# Development server with auto-reload
uv run uvicorn ticket_service.main:app --reload

# Production server
uv run uvicorn ticket_service.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Interactive documentation available at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- `/api/v1/openapi.json` - OpenAPI specification

### Example API Usage

```bash
# Start OAuth flow
curl -X GET "http://localhost:8000/api/v1/auth/login"

# Create ticket (after OAuth)
curl -X POST "http://localhost:8000/api/v1/tickets" \
  -H "X-User-ID: user-id" \
  -H "X-Project-Key: PROJ" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug Report",
    "description": "System issue",
    "reporter": "user@example.com",
    "priority": "high"
  }'
```

## Testing

The service includes comprehensive tests covering all endpoints and authentication flows:

### Test Structure

**test_ticket_service.py** - FastAPI endpoint testing
- Authentication flow testing
- CRUD operation endpoints
- Request/response validation
- Error handling and status codes
- Dependency injection testing

### Test Categories

- **Authentication Endpoints**: OAuth flow and token management
- **Ticket Endpoints**: Complete CRUD operations
- **Comment Endpoints**: Comment creation and retrieval
- **Validation**: Request/response model validation
- **Error Handling**: HTTP status codes and error responses
- **Dependencies**: Service injection and configuration

### Running Tests

```bash
# All service tests
uv run pytest src/ticket_service/tests/ -v

# Specific endpoint tests
uv run pytest src/ticket_service/tests/test_ticket_service.py::test_create_ticket -v

# Coverage reporting
uv run pytest src/ticket_service/tests/ --cov=ticket_service --cov-report=term-missing
```

### Test Strategy

Tests use FastAPI's `TestClient` for endpoint testing:
- Mock service implementations
- Request/response validation
- Authentication header testing
- Error scenario validation

## Configuration

### Environment Variables

```bash
# OAuth Configuration
OAUTH_CLIENT_ID="your-jira-oauth-client-id"
OAUTH_CLIENT_SECRET="your-jira-oauth-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8000/api/v1/auth/callback"

# Service Configuration
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
LOG_LEVEL="INFO"
```

### Dependency Injection

The service uses FastAPI's dependency injection system:

```python
async def get_ticket_service(
    user_id: str = Depends(get_user_id),
    project_key: str = Depends(get_project_key)
) -> TicketServiceAPI:
    return TicketImpl(user_id=user_id, project_key=project_key)
```

## Architecture

### Request Flow

```
HTTP Request → FastAPI Router → Dependencies → Service Implementation → Response
     ↓              ↓              ↓                    ↓                ↓
Validation → Authentication → Service Injection → Business Logic → JSON Response
```

### Key Components

- **FastAPI App**: Main application with routing and middleware
- **Dependencies**: Authentication and service injection
- **Models**: Request/response validation with Pydantic
- **Error Handling**: HTTP status code mapping
- **CORS**: Cross-origin resource sharing configuration

## Security

### Authentication

- OAuth 2.0 integration with Jira Cloud
- CSRF protection using state parameters
- Secure token storage and management
- User-scoped data access

### Request Validation

- Automatic input validation with Pydantic
- Content-Type validation
- Required header enforcement
- SQL injection prevention

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY src/ ./src/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0"]
```

### Production Considerations

- Use HTTPS in production
- Configure proper CORS origins
- Set up logging and monitoring
- Use environment-based configuration
- Implement rate limiting

## Dependencies

- `ticket_api` - Abstract interface and domain models
- `ticket_impl` - Jira implementation backend
- `fastapi` - Web framework
- `pydantic` - Data validation
- `uvicorn` - ASGI server