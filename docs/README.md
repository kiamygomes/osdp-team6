# Documentation

Comprehensive documentation for the AI-powered Ticket Management System.

## Documentation Files

### [Testing Guide](testing.md)
Complete testing strategy and how to run tests.

**Covers:**
- Test organization (unit, integration, E2E)
- Running tests with coverage
- Mocking strategies
- Authentication for tests
- Interface compliance verification
- Coverage requirements and current status

**Key Sections:**
- Unit Tests: Fast, isolated tests with mocked dependencies
- Integration Tests: Component interaction tests
- Coverage: 90.56% (436+ tests)

### [Telemetry and Observability](telemetry.md)
Monitoring, metrics, and observability setup.

**Covers:**
- Prometheus metrics collection
- Available metrics (latency, success rate, active requests)
- Integration with monitoring platforms (Prometheus, Grafana, Datadog)
- Example Prometheus queries
- Alerting rules
- Local testing of metrics
- Testing telemetry functionality

**Metrics:**
- `http_request_duration_seconds`: Request latency histogram
- `http_requests_total`: Total request count
- `http_requests_success_total`: Successful requests (2xx)
- `http_requests_failure_total`: Failed requests (4xx, 5xx)
- `http_requests_active`: Currently active requests
- `ticket_operations_total`: Ticket operations by type

### [Component Architecture](component.md)
Detailed breakdown of system components and their interactions.

**Covers:**
- Core components and responsibilities
- Data flow through the system
- Integration points
- Configuration for each component
- Error handling patterns

### [API Documentation](api/)
OpenAPI/Swagger documentation for REST endpoints.

**Includes:**
- Ticket Service API endpoints
- Request/response schemas
- Authentication requirements
- Error responses
- Example requests

## Quick Links

### Getting Started
1. Read [../README.md](../README.md) for project overview
2. Check [../DESIGN.md](../DESIGN.md) for architecture details
3. Review [testing.md](testing.md) for testing strategy

### For Developers
- [testing.md](testing.md): How to run tests
- [telemetry.md](telemetry.md): Monitoring your changes
- [component.md](component.md): Understanding the architecture
- [../DEPLOYMENT.md](../DEPLOYMENT.md): Deploying to production

### For DevOps/Infrastructure
- [../DEPLOYMENT.md](../DEPLOYMENT.md): Deployment guide
- [telemetry.md](telemetry.md): Monitoring setup
- [../terraform/README.md](../terraform/README.md): Infrastructure as code

### For API Consumers
- [api/README.md](api/README.md): API documentation
- [../AUTHENTICATION.md](../AUTHENTICATION.md): OAuth setup

## Documentation Structure

```
docs/
├── README.md                 (This file - documentation index)
├── testing.md                (Testing strategy and guide)
├── telemetry.md             (Observability and metrics)
├── component.md              (System components and architecture)
└── api/
    ├── README.md             (API overview)
    └── openapi.json          (OpenAPI specification)
```

## Key Documentation Files at Root

- **[README.md](../README.md)**: Project overview and getting started
- **[DESIGN.md](../DESIGN.md)**: Detailed architecture and design decisions
- **[DEPLOYMENT.md](../DEPLOYMENT.md)**: Deployment guides and infrastructure setup
- **[AUTHENTICATION.md](../AUTHENTICATION.md)**: OAuth 2.0 authentication setup
- **[STATUS.md](../STATUS.md)**: Current project status and quality metrics

## Component Documentation

Each component has its own README:

- [ticket_api](../src/ticket_api/README.md): Abstract ticketing interface
- [ticket_impl](../src/ticket_impl/README.md): Jira Cloud implementation
- [ticket_service](../src/ticket_service/README.md): FastAPI web service
- [ticket_client_adapter](../src/ticket_client_adapter/README.md): Remote client adapter
- [ticket_client_generated](../src/ticket_client_generated/README.md): Auto-generated client
- [orchestrator](../src/orchestrator/README.md): Main orchestration service
- [ai_adapter](../src/ai_adapter/README.md): AI service integration
- [chat_api](../src/chat_api/README.md): Chat platform interface

## Building Documentation

The project uses MkDocs for building and serving documentation:

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build static site
mkdocs build
```

Documentation config: [../mkdocs.yml](../mkdocs.yml)

## Contributing to Documentation

When adding new features or components:

1. Update relevant component README
2. Update main [DESIGN.md](../DESIGN.md) if architecture changes
3. Update [testing.md](testing.md) with test coverage
4. Update [telemetry.md](telemetry.md) if adding new metrics
5. Update [STATUS.md](../STATUS.md) with current status

## Documentation Standards

### READMEs
- Brief overview of purpose
- Installation/setup instructions
- Usage examples
- Configuration options
- Testing information
- Links to related documentation

### Design Documentation
- Architecture diagrams (ASCII art or Mermaid)
- Component responsibilities
- Data flow and interactions
- Design decisions and rationale
- Deployment considerations

### API Documentation
- Endpoint descriptions
- Request/response formats
- Authentication requirements
- Error codes and messages
- Example requests/responses

## Search and Navigation

Use the full documentation structure to find what you need:

**By Role:**
- **Developer**: Start with [testing.md](testing.md) and component READMEs
- **DevOps**: See [../DEPLOYMENT.md](../DEPLOYMENT.md) and [telemetry.md](telemetry.md)
- **Architect**: Read [../DESIGN.md](../DESIGN.md) and [component.md](component.md)
- **API Consumer**: Check [api/](api/) and [../AUTHENTICATION.md](../AUTHENTICATION.md)

**By Task:**
- **Setting up**: [../README.md](../README.md) → component READMEs → [testing.md](testing.md)
- **Deploying**: [../DEPLOYMENT.md](../DEPLOYMENT.md) → [telemetry.md](telemetry.md) → monitoring setup
- **Testing**: [testing.md](testing.md) → component tests → [telemetry.md](telemetry.md)
- **Using API**: [../AUTHENTICATION.md](../AUTHENTICATION.md) → [api/](api/) → examples

## Status and Metrics

- **Coverage**: 90.56% (436+ tests)
- **Code Quality**: 100% passing (ruff, mypy)
- **Type Checking**: All files pass mypy
- **Last Updated**: 2025-12-19

See [../STATUS.md](../STATUS.md) for detailed quality metrics.
