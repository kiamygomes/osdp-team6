#!/usr/bin/env python3
"""Script to test and demonstrate monitoring features.

This script:
1. Starts the services
2. Makes various requests to generate metrics
3. Retrieves and displays metrics
4. Verifies that all required metrics are present
"""

import time
from http import HTTPStatus
from typing import Any

import httpx


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def make_requests(base_url: str, headers: dict[str, str]) -> None:
    """Make various requests to generate metrics."""
    print(f"Making requests to {base_url}...")

    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
        # Health check (should succeed)
        print("  ✓ GET /health")
        response = client.get("/health")
        assert response.status_code == HTTPStatus.OK

        # Create tickets (should succeed)
        for i in range(5):
            print(f"  ✓ POST /api/v1/tickets (#{i + 1})")
            response = client.post(
                "/api/v1/tickets",
                json={
                    "title": f"Test Ticket {i + 1}",
                    "description": f"Monitoring test ticket {i + 1}",
                    "reporter": "test-user",
                    "priority": "medium",
                },
            )
            if response.status_code == HTTPStatus.CREATED:
                print(f"    Created ticket: {response.json()['id']}")

        # List tickets (should succeed)
        print("  ✓ GET /api/v1/tickets")
        response = client.get("/api/v1/tickets")
        if response.status_code == HTTPStatus.OK:
            data = response.json()
            ticket_count = len(data.get("tickets", []))
            print(f"    Found {ticket_count} tickets")

        # Invalid request (should fail with 404)
        print("  ✗ GET /api/v1/tickets/invalid-id (expected 404)")
        try:
            response = client.get("/api/v1/tickets/00000000-0000-0000-0000-000000000000")
            print(f"    Status: {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")


def get_metrics(base_url: str) -> str:
    """Retrieve metrics from the service."""
    print(f"Retrieving metrics from {base_url}/metrics...")

    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{base_url}/metrics")
        assert response.status_code == HTTPStatus.OK
        return response.text


def parse_metrics(metrics_text: str) -> dict[str, Any]:
    """Parse Prometheus metrics text format."""
    metrics: dict[str, Any] = {}

    for raw_line in metrics_text.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse metric line: metric_name{labels} value
        metric_name = line.split("{")[0] if "{" in line else line.split()[0] if " " in line else line

        if metric_name not in metrics:
            metrics[metric_name] = []

        metrics[metric_name].append(line)

    return metrics


def verify_required_metrics(metrics: dict[str, Any], service_name: str) -> bool:
    """Verify that all required metrics are present."""
    print(f"\nVerifying required metrics for {service_name}...")

    required_metrics = [
        "request_duration_seconds",
        "requests_total",
        "requests_success_total",
        "requests_failure_total",
        "requests_active",
    ]

    if service_name == "orchestrator":
        required_metrics.extend(
            [
                "ai_requests_total",
                "ai_request_duration_seconds",
                "ticket_operations_total",
            ]
        )
    elif service_name == "ticket_service":
        required_metrics.extend(
            [
                "ticket_operations_total",
            ]
        )

    all_present = True
    for metric in required_metrics:
        # Check if any metric contains the required name
        found = any(metric in key for key in metrics)
        status = "✓" if found else "✗"
        print(f"  {status} {metric}")
        if not found:
            all_present = False

    if all_present:
        print(f"\n✅ All required metrics present for {service_name}")
    else:
        print(f"\n❌ Some metrics missing for {service_name}")

    return all_present


def display_sample_metrics(metrics: dict[str, Any]) -> None:
    """Display sample metrics."""
    max_lines_per_metric = 3
    max_metrics = 10

    print("\nSample Metrics:")
    print("-" * 80)

    # Display first few lines of each metric type
    for metric_name, lines in list(metrics.items())[:max_metrics]:
        print(f"\n{metric_name}:")
        for line in lines[:max_lines_per_metric]:
            print(f"  {line}")
        if len(lines) > max_lines_per_metric:
            print(f"  ... ({len(lines) - max_lines_per_metric} more lines)")


def main() -> None:
    """Run monitoring test script."""
    print_section("OSDP Ticket Bot - Monitoring Test")

    # Configuration
    ticket_service_url = "http://localhost:8000"
    orchestrator_url = "http://localhost:8080"
    headers = {
        "X-User-ID": "test-user",
        "X-Project-Key": "TEST",
    }

    # Test Ticket Service
    print_section("Testing Ticket Service")
    try:
        make_requests(ticket_service_url, headers)
        time.sleep(1)  # Allow metrics to be collected

        metrics_text = get_metrics(ticket_service_url)
        metrics = parse_metrics(metrics_text)

        display_sample_metrics(metrics)
        verify_required_metrics(metrics, "ticket_service")

    except Exception as e:
        print(f"❌ Error testing ticket service: {e}")
        print("   Make sure the service is running: uvicorn ticket_service.main:app --reload")

    # Test Orchestrator Service
    print_section("Testing Orchestrator Service")
    try:
        # Make some requests to orchestrator
        print(f"Making requests to {orchestrator_url}...")
        with httpx.Client(base_url=orchestrator_url, timeout=30.0) as client:
            print("  ✓ GET /health")
            response = client.get("/health")
            assert response.status_code == HTTPStatus.OK

            print("  ✓ GET /status")
            response = client.get("/status")
            assert response.status_code == HTTPStatus.OK

        time.sleep(1)  # Allow metrics to be collected

        metrics_text = get_metrics(orchestrator_url)
        metrics = parse_metrics(metrics_text)

        display_sample_metrics(metrics)
        verify_required_metrics(metrics, "orchestrator")

    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        print(
            "   Make sure the service is running: uvicorn orchestrator.orchestrator_service:app --reload"
        )

    print_section("Monitoring Test Complete")
    print("\nTo view metrics in your browser:")
    print(f"  - Ticket Service: {ticket_service_url}/metrics")
    print(f"  - Orchestrator: {orchestrator_url}/metrics")
    print("\nTo set up Prometheus and Grafana, see docs/monitoring.md")


if __name__ == "__main__":
    main()
