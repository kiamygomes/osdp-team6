# Architecture

The OSDP Jira Service implements a layered, component-based architecture that separates concerns and enables flexible deployment patterns.

## Architectural Principles

- **Component-Based Design**: Five distinct, self-contained components with single responsibilities
- **Interface-Implementation Separation**: Abstract contracts define "what", implementations define "how"
- **Dependency Injection**: Runtime selection of implementations through stable interfaces
- **OAuth 2.0 Integration**: Secure authentication with token management and refresh

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│               Client Applications                            │
│          (Web, Mobile, CLI, etc.)                           │
└──────────┬───────────────────────────────────┬───────────────┘
           │                                   │
           │ (HTTP/REST)                       │ (Direct)
           │                                   │
┌──────────▼──────────────────────────┐  ┌────▼─────────────────────────┐
│      ticket_client_adapter          │  │      ticket_impl             │
│   (Domain Interface Adapter)        │  │   (Jira Implementation)      │
│  • TicketServiceAPI interface      │  │  • Jira Cloud integration    │
│  • HTTP abstraction                 │  │  • OAuth token management   │
│  • Model conversion                 │  │  • Data mapping             │
│  • Error handling                   │  │  • UUID abstraction         │
└──────────┬──────────────────────────┘  └────────────────────────────┘
           │                                   │
           │                                   │ (TicketServiceAPI)
           │                                   │
           └───────────────────┬───────────────┘
                               │ HTTP/REST
                  ┌────────────▼──────────────────┐
                  │    ticket_service            │
                  │ (FastAPI HTTP Service)       │
                  │ • REST API endpoints         │
                  │ • Request/Response validation│
                  │ • OAuth 2.0 authentication   │
                  │ • OpenAPI documentation      │
                  └────────────┬──────────────────┘
                               │ HTTP/REST
                  ┌────────────▼──────────────────┐
                  │ ticket_client_generated      │
                  │  (Auto-Generated Client)     │
                  │ • Type-safe HTTP client      │
                  │ • Generated from OpenAPI     │
                  │ • Request/Response models    │
                  │ • Async/await support        │
                  └────────────┬──────────────────┘
                               │ Jira REST API
                  ┌────────────▼──────────────────┐
                  │  External Services           │
                  │  (Jira Cloud, Auth0, etc.)   │
                  └───────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              Core Abstractions                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────▼───────────┐
           │    ticket_api         │
           │ (Abstract Interface & │
           │       Models)         │
           │ • TicketServiceAPI    │
           │ • Domain models       │
           │ • Enums & types       │
           └───────────────────────┘
```

## Components

### 1. ticket_api (Foundation Layer)
**Purpose**: Abstract interface and data models

- `TicketServiceAPI` abstract base class
- `Ticket` and `Comment` frozen dataclass models
- `TicketStatus` and `TicketPriority` enumerations
- Type safety and contract enforcement

**Dependencies**: None (pure abstractions)  
**Used By**: All other components

### 2. ticket_impl (Integration Layer)
**Purpose**: Concrete implementation for Jira Cloud

- Implements `TicketServiceAPI` for Jira Cloud
- OAuth 2.0 authentication flows and token management
- UUID to Jira key mapping for clean abstractions
- Data transformation between domain and Jira models

**Dependencies**: `ticket_api`, Jira Cloud API, SQLAlchemy, httpx  
**Used By**: `ticket_service`

### 3. ticket_service (API Layer)
**Purpose**: FastAPI web service with REST endpoints

- HTTP REST API for ticketing operations
- Dependency injection for `TicketServiceAPI` implementations
- OpenAPI/Swagger documentation generation
- Request/response validation with Pydantic

**Dependencies**: `ticket_api`, `ticket_impl`, FastAPI  
**Used By**: Client applications, `ticket_client_generated`

### 4. ticket_client_generated (Client Layer)
**Purpose**: Auto-generated HTTP client

- Generated from OpenAPI specification
- Type-safe HTTP client methods
- Request serialization and response deserialization
- Authentication token management

**Dependencies**: httpx, Pydantic  
**Generated From**: `ticket_service` OpenAPI spec  
**Used By**: `ticket_client_adapter`, client applications

### 5. ticket_client_adapter (Adapter Layer)
**Purpose**: HTTP client adapter implementing abstract interface

- Implements `TicketServiceAPI` for remote service access
- Uses generated HTTP client internally
- Transparent remote access with identical method signatures
- HTTP error handling and mapping

**Dependencies**: `ticket_api`, `ticket_client_generated`  
**Used By**: Client applications preferring domain interfaces

## Data Flow

### Ticket Creation Flow

```
Client Request
    ↓
ServiceClientAdapter.create_ticket()
    ↓
HTTP POST /tickets
    ↓
FastAPI Endpoint
    ↓
Dependency Injection (get_ticket_service)
    ↓
JiraTicketService.create_ticket()
    ↓
OAuth Authentication
    ↓
Jira REST API Call
    ↓
Response Transformation
    ↓
Ticket Model Return
```

### Authentication Flow

```
User Authorization Request
    ↓
OAuth Authorization URL Generation
    ↓
User Consent (External Browser)
    ↓
Authorization Code Callback
    ↓
Token Exchange Request
    ↓
Access Token Storage
    ↓
API Request with Bearer Token
    ↓
Token Refresh (if expired)
```

## Design Patterns

### Abstract Factory Pattern
The `TicketServiceAPI` serves as an abstract factory for creating and managing tickets, with concrete implementations for different external services.

### Adapter Pattern
The `ticket_client_adapter` implements the adapter pattern, allowing remote HTTP services to be used through the same interface as local implementations.

### Dependency Injection Pattern
FastAPI's dependency injection system allows runtime selection of different `TicketServiceAPI` implementations based on configuration.

### Repository Pattern
The abstract interface follows the repository pattern, providing a consistent API for ticket operations regardless of the underlying storage or external service.

## Configuration Management

### Environment-Based Configuration
```python
# Development
ENVIRONMENT=development
JIRA_CLIENT_ID=dev_client_id
JIRA_REDIRECT_URI=http://localhost:8000/auth/callback

# Production  
ENVIRONMENT=production
JIRA_CLIENT_ID=prod_client_id
JIRA_REDIRECT_URI=https://app.example.com/auth/callback
```

### Service Selection
```python
async def get_ticket_service() -> TicketServiceAPI:
    service_type = os.getenv("TICKET_SERVICE_TYPE", "jira")
    
    if service_type == "jira":
        return JiraTicketService(...)
    elif service_type == "linear":
        return LinearTicketService(...)
    else:
        raise ValueError(f"Unsupported service: {service_type}")
```

## Security Architecture

### OAuth 2.0 Flow
1. **Authorization Request**: Redirect user to external service authorization
2. **User Consent**: User grants permissions in external service
3. **Authorization Code**: Service redirects back with authorization code
4. **Token Exchange**: Exchange code for access and refresh tokens
5. **Token Storage**: Securely store tokens with encryption
6. **API Access**: Use access token for authenticated API calls
7. **Token Refresh**: Automatically refresh expired tokens

### Security Measures
- HTTPS-only OAuth flows in production
- Secure token storage with encryption
- Minimal OAuth scopes requested
- Token rotation and expiration handling
- Input validation and sanitization
- Rate limiting and abuse prevention

## Scalability Considerations

### Horizontal Scaling
- Stateless service design enables multiple instances
- Load balancer distributes requests across instances
- Shared token storage (Redis/Database) for session management

### Performance Optimization
- Connection pooling for HTTP clients
- Response caching for frequently accessed data
- Async/await throughout for non-blocking operations
- Database connection pooling and query optimization

### Monitoring and Observability
- Structured logging with correlation IDs
- Metrics collection for performance monitoring
- Health check endpoints for service monitoring
- Distributed tracing for request flow analysis

## Deployment Architecture

### Container Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY src/ ./src/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0"]
```

### Environment Separation
- **Development**: Local development with mock services
- **Staging**: Production-like environment for testing
- **Production**: Full production deployment with monitoring

### Infrastructure as Code
- Docker containers for consistent deployment
- Kubernetes manifests for orchestration
- Terraform for infrastructure provisioning
- CI/CD pipelines for automated deployment

## Testing Architecture

### Test Pyramid
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Component interaction and external service integration
- **End-to-End Tests**: Complete workflow validation
- **Contract Tests**: API contract validation between services

### Test Categories
- **ticket_api**: 100% coverage with contract validation
- **ticket_impl**: OAuth flow and external API integration testing
- **ticket_service**: FastAPI endpoint and dependency injection testing
- **ticket_client_adapter**: HTTP client and error handling testing

### Continuous Integration
- Automated test execution on every commit
- Code quality checks (linting, type checking)
- Security scanning and dependency auditing
- Performance regression testing

## Future Enhancements

### Additional Integrations
- Linear ticketing system support
- GitHub Issues integration
- Azure DevOps work items
- ServiceNow incident management

### Advanced Features
- Real-time webhook notifications
- Bulk operations and batch processing
- Advanced search and filtering
- Analytics and reporting dashboards
- Workflow automation and rules engine

### Performance Improvements
- GraphQL API for flexible data fetching
- Event-driven architecture with message queues
- Caching layers for improved response times
- Database sharding for large-scale deployments

This architecture provides a solid foundation for a scalable, maintainable ticketing microservice that can adapt to various external systems while maintaining clean separation of concerns and professional development practices.