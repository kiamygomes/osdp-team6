# Testing Guide

This document explains the testing strategy and how to run tests.

## Test Organization

### Unit Tests (`src/*/tests/`)
Fast, isolated tests with mocked dependencies:
- **ticket_api**: 22 tests, 100% coverage
- **ticket_impl**: 30+ tests, 95%+ coverage  
- **ticket_service**: 25+ tests, 90%+ coverage
- **ticket_service/telemetry**: 8 tests, 96% coverage ⭐ NEW
- **ticket_client_adapter**: 50+ tests, 95%+ coverage

### Integration Tests (`tests/integration/`)
Component interaction tests:
- Service + adapter integration
- Model conversion
- Error handling
- Telemetry and observability
- 15+ tests

### Overall Coverage
- **Current**: 90.56% (436+ tests)
- **Target**: ≥90% ✅
- **Files with full coverage**: 18 packages

## Running Tests

### All Tests
```bash
uv run pytest
```

### Unit Tests (Fast)
```bash
uv run pytest src/ -v
```

### Integration Tests
```bash
uv run pytest tests/integration/ -v
```

### Specific Component
```bash
uv run pytest src/ticket_api/tests/ -v
uv run pytest src/ticket_impl/tests/ -v
uv run pytest src/ticket_service/tests/ -v
uv run pytest src/ticket_client_adapter/tests/ -v
```

### With Coverage
```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Mocking Strategy

### Always Mocked
- Jira API (`httpx.AsyncClient` responses)
- OAuth token exchange (`exchange_code_for_tokens`, `get_valid_access_token`)

### Sometimes Mocked
- Database (in-memory SQLite for speed)
- HTTP service (in adapter tests)

### Never Mocked
- Domain models (`Ticket`, `Comment`)
- Interface contract (`TicketServiceAPI`)
- Generated client (in integration tests)

## Authentication for Tests

Tests use "test-" prefixed user IDs to bypass OAuth:

```python
# In tests
service = TicketImpl(user_id="test-user-001", project_key="PROJ")
```

Required headers for service tests:
- `X-User-ID: test-user-001`
- `X-Project-Key: PROJ`

## Interface Compliance

Verified through:
1. **MyPy**: Static type checking
2. **ABC enforcement**: Python prevents instantiation if methods missing
3. **Contract tests**: Both `TicketImpl` and `RemoteTicketService` pass same tests
4. **Integration tests**: Adapter used as `TicketServiceAPI` type

## Coverage Requirements

Minimum 90% coverage for all components.

**Current coverage (90.56% - PASSING):**
- ticket_api: 100%
- ticket_impl: 95%+
- ticket_service: 90%+
- ticket_service/telemetry: 96% ⭐
- ticket_client_adapter: 95%+
- orchestrator: 91%+
- ai_adapter: 89%+

## Recent Improvements

### Telemetry Test Suite (New)
Added comprehensive test coverage for observability and monitoring:
- PrometheusMiddleware endpoint normalization tests
- Request metrics collection and tracking
- Metrics export and Prometheus format validation
- Ticket operation tracking for success and failure scenarios

### Type Safety Enhancements
- Fixed mypy warnings with proper dataclass type guards
- All 58+ source files passing mypy strict type checking

### Code Quality
- Fixed ruff line length violations
- All imports properly formatted
- 100% of checks passing

## CI/CD

Tests run on CircleCI for each commit. All tests must:
- Pass locally before pushing
- Maintain 90%+ coverage
- Not require local credentials (use "test-" user IDs)
