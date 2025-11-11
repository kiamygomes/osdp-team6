# Integration Tests

This directory contains integration tests that verify component interactions in the ticket service.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
└── integration/
    └── test_service_adapter_integration.py  # Service + adapter tests
```

## Test Categories

### Integration Tests (`tests/integration/`)

Tests verify that multiple components work together:

- **Service endpoints**: FastAPI endpoints with mocked `TicketImpl`
- **Adapter integration**: `RemoteTicketService` with mocked HTTP responses
- **Model conversion**: Domain models ↔ generated models
- **Error handling**: HTTP status codes and exception mapping

## Running Tests

```bash
# All integration tests
uv run pytest tests/integration/ -v

# Specific test file
uv run pytest tests/integration/test_service_adapter_integration.py -v

# With coverage
uv run pytest tests/integration/ --cov=src --cov-report=term-missing
```

## Test Fixtures

Shared fixtures in `conftest.py`:

- **event_loop**: Event loop for async tests
- **mock_ticket_service**: Mock `TicketServiceAPI` implementation
- **sample_ticket**: Sample ticket for tests

## Authentication for Tests

Tests use "test-" prefixed user IDs (e.g., "test-user-001") to bypass OAuth verification.

Required headers:
- `X-User-ID`: User identifier (use "test-" prefix)
- `X-Project-Key`: Jira project key

## Mocking Strategy

- **Always mocked**: Jira API (`httpx.AsyncClient`), OAuth token exchange
- **Sometimes mocked**: Database (in-memory SQLite)
- **Never mocked**: Domain models, interface contract

## Adding New Tests

1. Create test file in `tests/integration/`
2. Use `@pytest.mark.integration` decorator
3. Use fixtures from `conftest.py`
4. Mock external dependencies
5. Use "test-" prefixed user IDs

Example:
```python
@pytest.mark.integration
def test_new_feature(sample_ticket):
    """Test description."""
    with patch("ticket_service.main.get_ticket_service") as mock:
        mock_service = AsyncMock()
        mock_service.create_ticket.return_value = sample_ticket
        mock.return_value = mock_service
        
        response = client.post("/api/v1/tickets", json={...})
        assert response.status_code == 201
```
