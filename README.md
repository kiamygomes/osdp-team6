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

### ticket_api - Foundation Layer
Abstract interface and data models defining the ticketing contract:
- `TicketServiceAPI` abstract base class with all required operations
- `Ticket` and `Comment` Pydantic models with validation
- `TicketStatus` and `TicketPriority` enumerations
- 100% test coverage with comprehensive validation

### ticket_impl - Jira Integration
Concrete implementation for Jira Cloud with OAuth 2.0:
- Complete Jira REST API v3 integration
- OAuth token management and refresh
- UUID to Jira key mapping for clean abstractions
- Data transformation between domain and Jira models

### ticket_service - HTTP API
FastAPI web service exposing REST endpoints:
- Complete CRUD operations for tickets and comments
- OAuth 2.0 authentication flow endpoints
- Automatic OpenAPI documentation generation
- Request/response validation with Pydantic

### ticket_client_generated - HTTP Client
Auto-generated type-safe client from OpenAPI specification:
- Generated Pydantic models for all requests/responses
- Async and sync operation support
- Comprehensive error handling
- Full OpenAPI 3.0 compatibility

### ticket_client_adapter - Domain Interface
Adapter wrapping the generated client with clean domain interface:
- Implements `TicketServiceAPI` for remote service access
- Hides HTTP/network details from business logic
- Model conversion between HTTP and domain models
- Connection management and error translation