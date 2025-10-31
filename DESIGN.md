# Design Document: OSDP Jira Service Architecture

## Introduction

This document describes the architecture and design decisions for the OSDP Jira Service, a professional-grade microservice system for ticketing integration. The system demonstrates modern Python development practices through a distributed ticketing service with OAuth 2.0 authentication, clean abstractions, dependency injection, and comprehensive testing.

## Application Goal

The OSDP Jira Service provides a flexible, extensible platform for integrating with various ticketing systems (Jira, Linear, GitHub Issues, etc.) through a unified interface. The system emphasizes strict separation of concerns, interface-implementation patterns, and automated quality assurance to create maintainable, scalable ticketing infrastructure that can adapt to different external services without changing core business logic.

## System Architecture

The ticketing service follows a layered, component-based architecture that separates concerns and enables flexible deployment patterns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
├─────────────────────────────────────────────────────────────┤
│              ticket_client_adapter                          │
│           (HTTP Client Implementation)                      │
├─────────────────────────────────────────────────────────────┤
│                 ticket_service                              │
│              (FastAPI Web Service)                          │
├─────────────────────────────────────────────────────────────┤
│                  ticket_impl                                │
│         (Jira/External Service Integration)                 │
├─────────────────────────────────────────────────────────────┤
│                  ticket_api                                 │
│        (Abstract Interface & Data Models)                   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Ticket API (`ticket_api`)
**Abstract interface and data models for ticketing operations**

The foundation layer that defines the contract for all ticketing operations without any implementation details.

#### Data Models

**Ticket Model:**
```python
class Ticket(BaseModel):
    id: UUID
    title: str                    # 1-200 characters
    description: str              # 1-5000 characters  
    status: TicketStatus         # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    priority: TicketPriority     # LOW, MEDIUM, HIGH, CRITICAL
    assignee: str | None         # Optional assignee email/username
    reporter: str                # Reporter email/username
    created_at: datetime         # UTC timestamp
    updated_at: datetime         # UTC timestamp
    comments: list[Comment]      # Associated comments
```

**Comment Model:**
```python
class Comment(BaseModel):
    id: UUID
    ticket_id: UUID              # Parent ticket reference
    author: str                  # Comment author email/username
    content: str                 # 1-2000 characters
    created_at: datetime         # UTC timestamp
    
    model_config = ConfigDict(frozen=True)  # Immutable
```

**Enumerations:**
- `TicketStatus`: Defines workflow states (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- `TicketPriority`: Defines importance levels (LOW, MEDIUM, HIGH, CRITICAL)

#### Abstract Interface

**TicketServiceAPI:**
```python
class TicketServiceAPI(ABC):
    @abstractmethod
    async def create_ticket(self, title: str, description: str, reporter: str, 
                          priority: TicketPriority = TicketPriority.MEDIUM,
                          assignee: str | None = None) -> Ticket
    
    @abstractmethod
    async def get_ticket(self, ticket_id: UUID) -> Ticket | None
    
    @abstractmethod
    async def list_tickets(self, status: TicketStatus | None = None,
                         assignee: str | None = None, reporter: str | None = None,
                         limit: int = 100, offset: int = 0) -> list[Ticket]
    
    @abstractmethod
    async def update_ticket(self, ticket_id: UUID, title: str | None = None,
                          description: str | None = None, status: TicketStatus | None = None,
                          priority: TicketPriority | None = None,
                          assignee: str | None = None) -> Ticket | None
    
    @abstractmethod
    async def delete_ticket(self, ticket_id: UUID) -> bool
    
    @abstractmethod
    async def add_comment(self, ticket_id: UUID, author: str, content: str) -> Comment | None
    
    @abstractmethod
    async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]
```

#### Design Principles

- **Immutability**: Comments are immutable once created to maintain audit trails
- **Validation**: Comprehensive field validation using Pydantic models
- **Type Safety**: Full type hints for all methods and models
- **Extensibility**: Easy to add new fields or operations without breaking existing code
- **Business Logic**: Ticket model includes methods for common operations (add_comment, update_status, assign_to)

### 2. Ticket Implementation (`ticket_impl`)
**Concrete implementations for external ticketing services**

This layer provides concrete implementations of the `TicketServiceAPI` for specific external services.

#### Jira Implementation

**JiraTicketService:**
```python
class JiraTicketService(TicketServiceAPI):
    def __init__(self, base_url: str, oauth_client: OAuthClient):
        self.base_url = base_url
        self.oauth_client = oauth_client
    
    async def create_ticket(self, title: str, description: str, reporter: str, 
                          priority: TicketPriority = TicketPriority.MEDIUM,
                          assignee: str | None = None) -> Ticket:
        # Maps to Jira's POST /rest/api/3/issue
        jira_issue = {
            "fields": {
                "project": {"key": "PROJ"},
                "summary": title,
                "description": description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": priority.value.title()},
                "assignee": {"emailAddress": assignee} if assignee else None,
                "reporter": {"emailAddress": reporter}
            }
        }
        # Implementation details...
```

#### OAuth 2.0 Integration

**Authentication Flow:**
1. **Authorization Request**: Redirect user to Jira OAuth authorization endpoint
2. **Authorization Grant**: User grants permission, receives authorization code
3. **Access Token Request**: Exchange authorization code for access token
4. **Token Storage**: Store access and refresh tokens securely
5. **Token Refresh**: Automatically refresh expired tokens

**OAuthClient:**
```python
class OAuthClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    async def get_authorization_url(self) -> str:
        # Generate OAuth authorization URL
    
    async def exchange_code_for_token(self, code: str) -> TokenResponse:
        # Exchange authorization code for access token
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        # Refresh expired access token
```

### 3. Ticket Service (`ticket_service`)
**FastAPI web service exposing ticketing operations through REST endpoints**

This layer provides HTTP endpoints that expose ticketing functionality through a REST API.

#### FastAPI Endpoints

**Ticket Operations:**
```python
@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(request: CreateTicketRequest, 
                       service: TicketServiceAPI = Depends(get_ticket_service)):
    return await service.create_ticket(
        title=request.title,
        description=request.description,
        reporter=request.reporter,
        priority=request.priority,
        assignee=request.assignee
    )

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: UUID,
                    service: TicketServiceAPI = Depends(get_ticket_service)):
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(status: TicketStatus | None = None,
                      assignee: str | None = None,
                      reporter: str | None = None,
                      limit: int = 100,
                      offset: int = 0,
                      service: TicketServiceAPI = Depends(get_ticket_service)):
    return await service.list_tickets(status, assignee, reporter, limit, offset)
```

**Comment Operations:**
```python
@app.post("/tickets/{ticket_id}/comments", response_model=CommentResponse)
async def add_comment(ticket_id: UUID, request: AddCommentRequest,
                     service: TicketServiceAPI = Depends(get_ticket_service)):
    comment = await service.add_comment(ticket_id, request.author, request.content)
    if not comment:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return comment

@app.get("/tickets/{ticket_id}/comments", response_model=list[CommentResponse])
async def get_comments(ticket_id: UUID,
                      service: TicketServiceAPI = Depends(get_ticket_service)):
    return await service.get_ticket_comments(ticket_id)
```

#### Dependency Injection

**Service Factory:**
```python
async def get_ticket_service() -> TicketServiceAPI:
    # Environment-based service selection
    service_type = os.getenv("TICKET_SERVICE_TYPE", "jira")
    
    if service_type == "jira":
        oauth_client = OAuthClient(
            client_id=os.getenv("JIRA_CLIENT_ID"),
            client_secret=os.getenv("JIRA_CLIENT_SECRET"),
            redirect_uri=os.getenv("JIRA_REDIRECT_URI")
        )
        return JiraTicketService(
            base_url=os.getenv("JIRA_BASE_URL"),
            oauth_client=oauth_client
        )
    else:
        raise ValueError(f"Unsupported service type: {service_type}")
```

#### Error Handling

**HTTP Status Code Mapping:**
- `200 OK`: Successful operations
- `201 Created`: Successful ticket/comment creation
- `404 Not Found`: Ticket not found
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Service errors

### 4. Ticket Client Generated (`ticket_client_generated`)
**Auto-generated HTTP client code for type-safe API interactions**

This component provides auto-generated client code based on the OpenAPI specification from the FastAPI service.

#### Generated Client Structure

**Client Class:**
```python
class TicketClient:
    def __init__(self, base_url: str, auth_token: str | None = None):
        self.base_url = base_url
        self.auth_token = auth_token
    
    async def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        # Auto-generated HTTP client method
    
    async def get_ticket(self, ticket_id: UUID) -> TicketResponse:
        # Auto-generated HTTP client method
    
    async def list_tickets(self, status: TicketStatus | None = None,
                          assignee: str | None = None,
                          reporter: str | None = None,
                          limit: int = 100,
                          offset: int = 0) -> list[TicketResponse]:
        # Auto-generated HTTP client method
```

### 5. Ticket Client Adapter (`ticket_client_adapter`)
**HTTP client adapter implementing the TicketServiceAPI interface**

This layer provides a local implementation of the `TicketServiceAPI` that communicates with the remote FastAPI service.

#### ServiceClientAdapter

**Implementation:**
```python
class ServiceClientAdapter(TicketServiceAPI):
    def __init__(self, base_url: str, auth_token: str | None = None):
        self._client = TicketClient(base_url=base_url, auth_token=auth_token)
    
    async def create_ticket(self, title: str, description: str, reporter: str,
                          priority: TicketPriority = TicketPriority.MEDIUM,
                          assignee: str | None = None) -> Ticket:
        request = CreateTicketRequest(
            title=title,
            description=description,
            reporter=reporter,
            priority=priority,
            assignee=assignee
        )
        response = await self._client.create_ticket(request)
        return self._convert_response_to_ticket(response)
    
    async def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        try:
            response = await self._client.get_ticket(ticket_id)
            return self._convert_response_to_ticket(response)
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise
```

## Data Flow Architecture

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

## Testing Strategy

### Test Categories

**Unit Tests (`src/*/tests/`):**
- **ticket_api**: Contract validation, model validation, enum testing, abstract interface enforcement
- **ticket_impl**: OAuth flow testing, Jira API integration (mocked), error handling
- **ticket_service**: FastAPI endpoint testing, dependency injection, request/response validation
- **ticket_client_adapter**: HTTP client testing, response transformation, error mapping

**Integration Tests (`tests/integration/`):**
- Component interaction testing
- OAuth authentication flow validation
- Service-to-service communication
- Database integration (if applicable)

**End-to-End Tests (`tests/e2e/`):**
- Complete workflow testing
- Real external service integration
- Performance and load testing

### Test Coverage Requirements

- **Minimum Coverage**: 90% for all components
- **ticket_api**: 100% coverage (achieved)
- **Critical Paths**: 100% coverage for authentication and data validation
- **Error Scenarios**: Comprehensive error condition testing

### Mocking Strategy

**External Service Mocking:**
```python
@pytest.fixture
def mock_jira_client():
    with patch('ticket_impl.jira.JiraClient') as mock:
        mock.return_value.create_issue.return_value = {
            "id": "PROJ-123",
            "key": "PROJ-123",
            "fields": {
                "summary": "Test Issue",
                "description": "Test Description"
            }
        }
        yield mock
```

**OAuth Mocking:**
```python
@pytest.fixture
def mock_oauth_client():
    with patch('ticket_impl.oauth.OAuthClient') as mock:
        mock.return_value.get_access_token.return_value = "mock_token"
        yield mock
```

## Security Considerations

### OAuth 2.0 Security

- **Token Storage**: Secure storage of access and refresh tokens
- **Token Rotation**: Automatic refresh token rotation
- **Scope Limitation**: Minimal required OAuth scopes
- **HTTPS Only**: All OAuth flows require HTTPS in production

### API Security

- **Authentication**: Bearer token authentication for all endpoints
- **Authorization**: Role-based access control (if applicable)
- **Input Validation**: Comprehensive request validation using Pydantic
- **Rate Limiting**: API rate limiting to prevent abuse

### Data Protection

- **PII Handling**: Careful handling of personally identifiable information
- **Audit Logging**: Comprehensive audit trails for all operations
- **Data Encryption**: Encryption at rest and in transit

## Deployment Architecture

### Environment Configuration

**Development Environment:**
```bash
ENVIRONMENT=development
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_CLIENT_ID=your_dev_client_id
JIRA_CLIENT_SECRET=your_dev_client_secret
JIRA_REDIRECT_URI=http://localhost:8000/auth/callback
```

**Production Environment:**
```bash
ENVIRONMENT=production
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_CLIENT_ID=your_prod_client_id
JIRA_CLIENT_SECRET=your_prod_client_secret
JIRA_REDIRECT_URI=https://your-app.herokuapp.com/auth/callback
```

### Containerization

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY src/ ./src/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scalability Considerations

- **Horizontal Scaling**: Stateless service design enables horizontal scaling
- **Load Balancing**: Support for multiple service instances
- **Caching**: Redis caching for frequently accessed tickets
- **Database**: PostgreSQL for persistent ticket storage (if needed)

## Future Enhancements

### Additional Integrations

- **Linear Integration**: Support for Linear ticketing system
- **GitHub Issues**: Integration with GitHub Issues API
- **Azure DevOps**: Support for Azure DevOps work items
- **ServiceNow**: Enterprise service management integration

### Advanced Features

- **Webhook Support**: Real-time notifications for ticket updates
- **Bulk Operations**: Batch ticket creation and updates
- **Advanced Search**: Full-text search and complex filtering
- **Reporting**: Analytics and reporting capabilities
- **Workflow Automation**: Custom workflow rules and automation

### Performance Optimizations

- **Async Processing**: Background job processing for heavy operations
- **Connection Pooling**: Optimized HTTP connection management
- **Response Caching**: Intelligent caching strategies
- **Database Optimization**: Query optimization and indexing strategies

## Conclusion

The OSDP Jira Service architecture provides a robust, scalable foundation for ticketing system integration. The component-based design with clear separation of concerns enables easy maintenance, testing, and extension. The OAuth 2.0 integration ensures secure access to external services, while the comprehensive testing strategy provides confidence in system reliability.

The architecture successfully demonstrates modern Python development practices and provides a template for building similar microservice systems with external API integration requirements.