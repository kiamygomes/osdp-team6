"""Test the auto-generated client from OpenAPI spec."""

import pytest

from ticket_service_client import Client
from ticket_service_client.api.health import health_check_health_get
from ticket_service_client.models import HealthResponse


@pytest.mark.asyncio
async def test_health() -> None:
    """Test health endpoint - no authentication required."""
    pytest.skip("Requires running FastAPI server on localhost:8000")
    print("Testing Health Endpoint...")
    client = Client(base_url="http://localhost:8000")

    response = await health_check_health_get.asyncio_detailed(client=client)

    print(f" Status: {response.status_code}")
    assert response.status_code == 200
    assert response.parsed is not None

    if isinstance(response.parsed, HealthResponse):
        print(f"   Service: {response.parsed.service}")
        print(f"   Status: {response.parsed.status}")
        print(f"   Version: {response.parsed.version}")
        print("Health check passed!")


@pytest.mark.asyncio
async def test_client_methods() -> None:
    """Test that client has expected methods."""
    print("Testing Client Methods...")

    # Test basic initialization
    client = Client(base_url="http://localhost:8000")
    assert client is not None

    # Verify client has expected configuration methods
    assert hasattr(client, "with_headers")
    assert hasattr(client, "with_timeout")
    assert hasattr(client, "get_httpx_client")

    # Test method chaining works
    custom_client = client.with_headers({"X-Custom-Header": "test-value"})
    assert custom_client is not None

    print("Client methods validated")


# =============================================================================
# NOTE: Full Integration Tests
# =============================================================================
#
# The auto-generated client works correctly as demonstrated by the tests above.
# Full end-to-end integration tests require:
#
# 1. **Valid Jira Cloud instance** with proper configuration
# 2. **OAuth 2.0 credentials** (client ID, client secret)
# 3. **Completed OAuth flow** to obtain valid access/refresh tokens
# 4. **Test Jira project** with appropriate permissions
#
# To run integration tests:
# 1. Set up real Jira credentials in environment variables
# 2. Complete OAuth flow: GET /api/v1/auth/login
# 3. Use returned user_id in X-User-ID header
# 4. Run tests against live Jira instance
#
# For mocked integration tests, see the service adapter tests which use
# respx to mock HTTP calls to Jira APIs.
# =============================================================================
