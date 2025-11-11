# OSDP Jira Service: Component-Based Ticketing Microservice

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://mypy-lang.org/)
[![Coverage](https://img.shields.io/badge/coverage-90%2B%25-brightgreen)](https://pytest-cov.readthedocs.io/)

This repository implements a professional-grade microservice for Jira/ticketing integration using component-based architecture. The system demonstrates modern Python development practices through a distributed ticketing service with OAuth 2.0 authentication, clean abstractions, and comprehensive testing.

The project emphasizes strict separation of concerns, interface-implementation patterns, dependency injection, and automated quality assurance to create maintainable, scalable ticketing infrastructure.

## Architectural Philosophy

This project implements a microservice architecture for ticketing systems, built on the principle of "programming integrated over time." The architecture combats complexity through clear boundaries and ensures the system remains maintainable and evolvable.

- **Component-Based Design:** The system is decomposed into distinct, self-contained components. Each component has a single responsibility and can be extracted for use in other projects with minimal effort.
- **Interface-Implementation Separation:** All functionality is defined by abstract contracts (ABCs) that specify "what" operations are available, fulfilled by concrete implementations that define "how" those operations work. This decouples business logic from specific technologies (like Jira, Linear, or GitHub Issues).
- **Dependency Injection:** Implementations are injected into abstract contracts at runtime, ensuring consumers depend only on stable interfaces rather than volatile implementation details.
- **OAuth 2.0 Integration:** Secure authentication and authorization for external ticketing services with token management and refresh capabilities.

## Core Components

The project is a `uv` workspace containing five primary packages that implement a complete ticketing microservice:

1. **`ticket_api`**: Defines the abstract `TicketServiceAPI` base class (ABC) and core data models (`Ticket`, `Comment`). This is the contract for what actions a ticketing service can perform (e.g., `create_ticket`, `add_comment`, `update_status`).

2. **`ticket_impl`**: Provides concrete implementations that integrate with external ticketing services like Jira, using OAuth 2.0 authentication to perform operations defined in the `TicketServiceAPI` abstraction.

3. **`ticket_service`**: FastAPI web service that exposes ticketing operations through REST endpoints, using dependency injection to work with any `TicketServiceAPI` implementation.

4. **`ticket_client_generated`**: Auto-generated HTTP client code for communicating with the ticket service, providing type-safe API interactions.

5. **`ticket_client_adapter`**: HTTP client adapter that implements the `TicketServiceAPI` interface for remote service access, enabling distributed ticketing functionality.

## Project Structure

```
osdp-jira-service/
├── src/                          # Source packages (uv workspace members)
│   ├── ticket_api/               # Abstract ticketing interface and data models
│   │   ├── src/ticket_api/       # Package source code
│   │   │   ├── __init__.py       # Package exports
│   │   │   ├── models.py         # Ticket, Comment, and enum models
│   │   │   ├── interface.py      # TicketServiceAPI abstract base class
│   │   │   └── py.typed          # Type checking marker
│   │   ├── tests/                # Unit tests for the API contract
│   │   ├── pyproject.toml        # Package configuration
│   │   └── README.md             # Package documentation
│   ├── ticket_impl/              # Jira/external service implementations
│   ├── ticket_service/           # FastAPI web service
│   ├── ticket_client_generated/  # Auto-generated HTTP client
│   └── ticket_client_adapter/    # HTTP client adapter
├── tests/                        # Integration and E2E tests
│   └── integration/              # Component integration tests
├── docs/                         # Documentation source files
├── .circleci/                    # CircleCI configuration
├── pyproject.toml               # Workspace configuration
├── uv.lock                      # Locked dependency versions
├── DESIGN.md                    # Architecture and design documentation
└── README.md                    # Project overview and setup
```

## Project Setup

### 1. Prerequisites

-   Python 3.11 or higher
-   `uv` – A fast, all-in-one Python package manager.

### 2. Initial Setup

1. **Install `uv`:**
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Windows (PowerShell)
   irm https://astral.sh/uv/install.ps1 | iex
   ```

2. **Clone the Repository:**
   ```bash
   git clone <your-repository-url>
   cd osdp-jira-service
   ```

3. **Set Up OAuth 2.0 Credentials:**
   - For Jira integration, create an OAuth 2.0 application in your Atlassian Developer Console
   - Configure redirect URIs for both development and production environments:
     - Development: `http://localhost:8000/auth/callback`
     - Production: `https://your-app.herokuapp.com/auth/callback`
   - Set environment variables for OAuth configuration:
     ```bash
     export JIRA_CLIENT_ID="your_client_id"
     export JIRA_CLIENT_SECRET="your_client_secret"
     export JIRA_REDIRECT_URI="http://localhost:8000/auth/callback"
     export ENVIRONMENT="development"  # or "production"
     ```
   - **Important:** Credential information is sensitive and should never be committed to version control.

4. **Create and Sync the Virtual Environment:**
   This command creates a `.venv` folder and installs all packages (including workspace members and development tools):
   ```bash
   uv sync --all-packages --extra dev
   ```

5. **Activate the Virtual Environment:**
   ```bash
   # macOS / Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

6. **Verify Installation:**
   Run the test suite to ensure everything is set up correctly:
   ```bash
   uv run pytest src/ticket_api/tests/ -v
   ```

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To start the FastAPI ticketing service:
```bash
uv run uvicorn ticket_service.main:app --reload
```

The service will be available at `http://localhost:8000` with interactive API documentation at `http://localhost:8000/docs`.

### Running the Toolchain

-   **Linting & Formatting (Ruff):**
    The project uses Ruff with comprehensive rules configured in `pyproject.toml`.
    ```bash
    # Check for issues
    uv run ruff check .
    # Automatically fix issues
    uv run ruff check . --fix
    # Check formatting
    uv run ruff format --check .
    # Apply formatting
    uv run ruff format .
    ```

-   **Static Type Checking (MyPy):**
    ```bash
    uv run mypy src tests
    ```

- **Testing (Pytest):**

  ```bash
  # Fast unit tests for development
  uv run pytest src/ -v

  # Component-specific test suites
  uv run pytest src/ticket_api/tests/ -v
  uv run pytest src/ticket_impl/tests/ -v
  uv run pytest src/ticket_service/tests/ -v

  # Integration and end-to-end tests
  uv run pytest tests/integration/ -v
  uv run pytest tests/e2e/ -v

  # Coverage reporting
  uv run pytest --cov=src --cov-report=html
  ```

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Testing Strategy

The project implements a comprehensive testing strategy with different test categories for various development scenarios:

### Test Categories

**Unit Tests** (`src/*/tests/`)
- Fast, isolated tests with mocked dependencies
- Focus on individual component behavior and contracts
- No external service dependencies
- Run in milliseconds for rapid feedback

**Integration Tests** (`tests/integration/`)
- Component interaction testing
- OAuth authentication flow validation
- Real HTTP client behavior with mocked responses
- Database and storage layer testing

**End-to-End Tests** (`tests/e2e/`)
- Complete application workflow validation
- Service startup and API interaction testing
- Full OAuth flow with real external services
- Performance and reliability testing

### Test Execution

```bash
# Fast unit tests (recommended for development)
uv run pytest src/ -v

# Component-specific tests
uv run pytest src/ticket_api/tests/ -v          # API contract tests
uv run pytest src/ticket_impl/tests/ -v         # Jira implementation tests
uv run pytest src/ticket_service/tests/ -v      # FastAPI service tests
uv run pytest src/ticket_client_adapter/tests/ -v  # HTTP client adapter tests

# Integration tests (requires OAuth setup)
uv run pytest tests/integration/ -v

# All tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# CI/CD compatible tests only
uv run pytest -m "not local_credentials"
```

### Test Markers

Tests are categorized using pytest markers:
- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.local_credentials` - Requires local OAuth setup

### Authentication Testing

The testing infrastructure handles different authentication scenarios:
- **Mock Authentication**: Unit tests use mocked OAuth responses
- **Environment Variables**: Integration tests use `JIRA_CLIENT_ID`, `JIRA_CLIENT_SECRET`
- **Test Users**: Special test user IDs bypass OAuth for development
- **Graceful Degradation**: Missing credentials skip tests with clear messages

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- **All Branches**: Unit tests, linting, and CI-compatible tests
- **Main/Develop**: Additional integration tests with real Gmail API calls
- **Artifacts**: Coverage reports, test results, and build summaries

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.

## Development Workflow

### Quick Start
1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest src/ticket_api/tests/ -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **Type checking**: `uv run mypy src/ticket_api/`
6. **View documentation**: `uv run mkdocs serve`

### Best Practices
- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify OAuth flows and external service interactions
- Run the ticket API tests (`uv run pytest src/ticket_api/tests/`) to validate the core contract
- The CircleCI pipeline provides automated validation on every push

## Component Overview

### 📦 ticket_api - Foundation Layer
**Abstract interface and data models defining the ticketing contract**

The foundation of the entire system, providing clean abstractions and type-safe models.

**Key Features:**
- `TicketServiceAPI` abstract base class with 10 required operations
- Immutable `Ticket` and `Comment` frozen dataclasses
- `TicketStatus` and `TicketPriority` enumerations
- Custom exception hierarchy (`TicketAPIError`, `ServiceError`, `TicketNotFoundError`)
- Zero external dependencies (pure Python stdlib)
- 100% test coverage (22 tests)

**Documentation:** See [`src/ticket_api/README.md`](src/ticket_api/README.md) for complete API reference, usage examples, and integration guide.

**Quick Example:**
```python
from ticket_api import Ticket, TicketStatus, TicketPriority

ticket = Ticket(
    title="Bug in login",
    description="Users cannot authenticate",
    reporter="user@example.com",
    priority=TicketPriority.HIGH
)
```

---

### 🔌 ticket_impl - Jira Cloud Integration
**Production-ready Jira Cloud implementation with OAuth 2.0**

Complete implementation of `TicketServiceAPI` that integrates directly with Jira Cloud REST API v3.

**Key Features:**
- Full Jira Cloud REST API v3 integration
- OAuth 2.0 (3-legged) authentication with automatic token refresh
- UUID abstraction (hides Jira issue keys from domain layer)
- Atlassian Document Format (ADF) support for rich text
- SQLAlchemy-based token and mapping storage
- Comprehensive error handling and logging

**Components:**
- `TicketImpl` - Main service implementation
- `jira_client` - Low-level HTTP client for Jira API
- `oauth` - OAuth 2.0 flow and token management
- `storage` - SQLite/PostgreSQL persistence layer
- `config` - Environment-based configuration

**Documentation:** See [`src/ticket_impl/README.md`](src/ticket_impl/README.md) for OAuth setup, Jira integration guide, and data transformation details.

**Quick Example:**
```python
from ticket_impl import TicketImpl

service = TicketImpl(user_id="user-123", project_key="PROJ")
ticket = await service.create_ticket(
    title="Bug Report",
    description="System issue",
    reporter="user@example.com"
)
```

---

### 🌐 ticket_service - FastAPI Web Service
**Production-ready REST API with cookie-based authentication**

FastAPI-based HTTP service exposing ticket operations through REST endpoints.

**Key Features:**
- RESTful API with 13 endpoints (tickets, comments, auth, health)
- Cookie-based session authentication (seamless for browsers)
- OAuth 2.0 integration for Jira Cloud
- Automatic OpenAPI/Swagger documentation
- Request/response validation with Pydantic
- CORS support for web applications
- Dependency injection for clean architecture

**Endpoints:**
- **Auth:** `/api/v1/auth/login`, `/api/v1/auth/callback`, `/api/v1/auth/status`, `/api/v1/auth/logout`
- **Tickets:** `POST /api/v1/tickets`, `GET /api/v1/tickets/{id}`, `GET /api/v1/tickets`, `PATCH /api/v1/tickets/{id}`, `DELETE /api/v1/tickets/{id}`
- **Comments:** `POST /api/v1/tickets/{id}/comments`, `GET /api/v1/tickets/{id}/comments`
- **Health:** `GET /health`

**Documentation:** See [`src/ticket_service/README.md`](src/ticket_service/README.md) for complete API reference, authentication guide, and deployment instructions.

**Quick Start:**
```bash
# Start the service
uv run uvicorn ticket_service.main:app --reload

# Visit interactive docs
open http://localhost:8000/docs
```

---

### 🤖 ticket_client_generated - Auto-Generated HTTP Client
**Type-safe HTTP client generated from OpenAPI specification**

Auto-generated client code providing type-safe API interactions with the ticket service.

**Key Features:**
- Generated from OpenAPI 3.0 specification
- Type-safe Pydantic models for all requests/responses
- Async and sync operation support
- Comprehensive error handling
- Automatic serialization/deserialization

**Documentation:** See [`src/ticket_client_generated/README.md`](src/ticket_client_generated/README.md) for generation process and usage examples.

**Quick Example:**
```python
from ticket_service_client import Client
from ticket_service_client.api.tickets import create_ticket_api_v1_tickets_post

client = Client(base_url="http://localhost:8000")
response = await create_ticket_api_v1_tickets_post.asyncio_detailed(
    client=client,
    body=TicketCreateRequest(...)
)
```

---

### 🔄 ticket_client_adapter - Remote Service Adapter
**Enterprise-grade HTTP client with reliability features**

Adapter wrapping the generated client with the clean `TicketServiceAPI` interface, adding production-critical reliability features.

**Key Features:**
- Implements `TicketServiceAPI` for location transparency
- **Idempotency:** Safe retries with idempotency keys
- **Retry Logic:** Exponential backoff with jitter for transient failures
- **Circuit Breaker:** Prevents cascading failures
- **Observability:** Correlation IDs and structured logging
- Hides all HTTP/network details from business logic

**Components:**
- `RemoteTicketService` - Main adapter implementing `TicketServiceAPI`
- `IdempotentClient` - Enhanced HTTP client with idempotency support
- `CircuitBreaker` - Fault tolerance mechanism

**Documentation:** See [`src/ticket_client_adapter/README.md`](src/ticket_client_adapter/README.md) for reliability features, retry strategies, and production configuration.

**Quick Example:**
```python
from ticket_client_adapter import RemoteTicketService

async with RemoteTicketService(
    base_url="http://localhost:8000",
    user_id="user-123",
    project_key="PROJ",
    max_retries=3
) as service:
    # Same interface as TicketImpl - no HTTP details!
    ticket = await service.create_ticket(
        title="Bug Report",
        description="System issue",
        reporter="user@example.com"
    )
```

---

## 📊 Test Coverage Summary

| Package | Tests | Coverage | Key Features Tested |
|---------|-------|----------|---------------------|
| **ticket_api** | 22 | 100% | Models, interface, exceptions, enums |
| **ticket_impl** | 30+ | 95%+ | Jira integration, OAuth, storage, UUID mapping |
| **ticket_service** | 25+ | 90%+ | REST endpoints, auth flow, validation |
| **ticket_client_adapter** | 50+ | 95%+ | HTTP client, retries, circuit breaker, idempotency |
| **Integration** | 15+ | N/A | Component interaction, end-to-end workflows |

**Total:** 140+ tests ensuring production-ready quality

---

## 🏗️ Architecture Patterns

### Interface-Implementation Separation
```python
# Define the contract (ticket_api)
class TicketServiceAPI(ABC):
    @abstractmethod
    async def create_ticket(...) -> Ticket: ...

# Implement for Jira (ticket_impl)
class TicketImpl(TicketServiceAPI):
    async def create_ticket(...) -> Ticket:
        # Jira-specific implementation

# Implement for remote HTTP (ticket_client_adapter)
class RemoteTicketService(TicketServiceAPI):
    async def create_ticket(...) -> Ticket:
        # HTTP client implementation
```

### Location Transparency
```python
# Same code works with local or remote implementation
def get_service() -> TicketServiceAPI:
    if USE_REMOTE:
        return RemoteTicketService(...)  # HTTP client
    else:
        return TicketImpl(...)  # Direct Jira

# Business logic doesn't care which implementation
service = get_service()
ticket = await service.create_ticket(...)
```

### Dependency Injection
```python
# FastAPI automatically injects the right implementation
@app.post("/api/v1/tickets")
async def create_ticket(
    request: TicketCreateRequest,
    service: Annotated[TicketServiceAPI, Depends(get_ticket_service)]
):
    return await service.create_ticket(...)
```

---

## 🚀 Production Deployment

### Render Deployment
The project includes `render.yaml` for one-click deployment to Render:
- Web service with auto-scaling
- PostgreSQL database
- Environment variable management
- Health check monitoring

### Docker Deployment
Each component can be containerized:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ ./src/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0"]
```

### Environment Configuration
```bash
# Jira OAuth
OAUTH_CLIENT_ID="your-client-id"
OAUTH_CLIENT_SECRET="your-client-secret"
OAUTH_REDIRECT_URI="https://your-app.com/api/v1/auth/callback"
JIRA_CLOUD_ID="your-cloud-id"

# Database
DB_URL="postgresql://user:pass@localhost/dbname"

# Service
CORS_ORIGINS="https://your-frontend.com"
LOG_LEVEL="INFO"
```

---

## 📚 Additional Documentation

- **[DESIGN.md](DESIGN.md)** - Architecture decisions and design patterns
- **[docs/testing.md](docs/testing.md)** - Comprehensive testing guide
- **[.env.example](.env.example)** - Environment variable template
- **Component READMEs** - Detailed documentation in each `src/*/README.md`

---

## 🤝 Contributing

1. **Code Quality:** All code must pass `ruff check`, `ruff format`, and `mypy`
2. **Testing:** Maintain 90%+ test coverage
3. **Documentation:** Update relevant README files
4. **Type Safety:** Full type annotations required
5. **Interface Compatibility:** Don't break `TicketServiceAPI` contract

---

## 📄 License

This project is part of the OSDP coursework and follows university guidelines.