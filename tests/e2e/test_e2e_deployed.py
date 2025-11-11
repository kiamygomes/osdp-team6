"""True end-to-end (E2E) tests for the deployed service on Render.

These tests hit the live FastAPI service deployed on Render using
real Jira OAuth credentials to verify:
1. Ticket creation works
2. Ticket retrieval works
3. Listing tickets works
"""

import os
from http import HTTPStatus
from uuid import UUID

import httpx
import pytest

pytestmark = pytest.mark.e2e

# --- Environment configuration ---
BASE_URL = os.getenv("BASE_URL", "https://osdp-team6.onrender.com")
OAUTH_USER_ID = os.getenv("OAUTH_USER_ID", "6b289e28-8530-4e2f-a8a7-6d2ec8dbe3c2")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")
OAUTH_REDIRECT_URI = os.getenv(
    "OAUTH_REDIRECT_URI",
    "https://osdp-team6.onrender.com/api/v1/auth/callback",
)


@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Deployed tests require browser OAuth, skip in CI",
)
class TestE2ETicketManagementDeployed:
    """End-to-end tests hitting the deployed service."""

    def test_create_and_get_ticket(self, deployed_client: httpx.Client) -> None:
        """Test creating and retrieving a ticket on deployed Render API."""
        payload = {
            "title": "E2E Deployed Test Ticket",
            "description": "Created against deployed Render instance.",
            "reporter": OAUTH_USER_ID,
            "priority": "high",
        }

        # Step 1: Create ticket
        resp = deployed_client.post("/api/v1/tickets", json=payload)

        # Fail hard if unauthorized or other issues
        assert resp.status_code == HTTPStatus.CREATED, f"Unexpected: {resp.status_code} → {resp.text[:150]}"

        data = resp.json()
        assert "id" in data, f"No ID in response: {data}"
        ticket_id = UUID(data["id"])
        assert data["title"] == payload["title"]
        assert data["priority"].lower() == "high"

        # Step 2: Retrieve the created ticket
        r2 = deployed_client.get(f"/api/v1/tickets/{ticket_id}")
        assert r2.status_code == HTTPStatus.OK, f"Retrieve failed: {r2.status_code} → {r2.text[:150]}"

        retrieved = r2.json()
        assert retrieved["id"] == str(ticket_id)
        assert retrieved["title"] == payload["title"]

    def test_list_tickets(self, deployed_client: httpx.Client) -> None:
        """Test listing tickets from the deployed Render API."""
        resp = deployed_client.get("/api/v1/tickets")

        assert resp.status_code == HTTPStatus.OK, f"Unexpected: {resp.status_code} → {resp.text[:150]}"
        data = resp.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)
