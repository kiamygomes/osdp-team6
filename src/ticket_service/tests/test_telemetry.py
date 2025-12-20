"""Unit tests for telemetry module in the Ticket Service."""

from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ticket_service.telemetry import (
    PrometheusMiddleware,
    get_metrics,
    track_ticket_operation,
)


@pytest.fixture
def app_with_middleware() -> FastAPI:
    """Create a FastAPI app with PrometheusMiddleware."""
    test_app = FastAPI()
    test_app.add_middleware(PrometheusMiddleware)

    @test_app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"message": "test"}

    @test_app.get("/test-error")
    async def test_error_endpoint() -> None:
        error_message = "Test error"
        raise ValueError(error_message)

    @test_app.get("/metrics")
    async def metrics_endpoint() -> str:
        return "metrics"

    return test_app


@pytest.fixture
def client(app_with_middleware: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app_with_middleware)


class TestPrometheusMiddleware:
    """Test the PrometheusMiddleware class."""

    def test_successful_request(self, client: TestClient) -> None:
        """Test metrics collection for successful requests."""
        response = client.get("/test")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"message": "test"}

    def test_metrics_endpoint_skipped(self, client: TestClient) -> None:
        """Test that metrics endpoint itself is not tracked."""
        response = client.get("/metrics")
        assert response.status_code == HTTPStatus.OK

    def test_failed_request(self, client: TestClient) -> None:
        """Test metrics collection for failed requests with exceptions."""
        expected_error = "Test error"
        with pytest.raises(ValueError, match=expected_error):
            client.get("/test-error")


class TestMetricsHelpers:
    """Test helper functions for metrics."""

    def test_track_ticket_operation_success(self) -> None:
        """Test tracking a successful ticket operation."""
        # This should not raise
        track_ticket_operation("create", "success")

    def test_track_ticket_operation_failure(self) -> None:
        """Test tracking a failed ticket operation."""
        # This should not raise
        track_ticket_operation("update", "failure")

    def test_get_metrics_returns_bytes(self) -> None:
        """Test that get_metrics returns bytes."""
        metrics = get_metrics()
        assert isinstance(metrics, bytes)
        assert len(metrics) > 0
        # Check that it contains some prometheus metrics
        assert b"http_request_duration_seconds" in metrics

    def test_get_metrics_contains_ticket_operations(self) -> None:
        """Test that metrics includes ticket operation counters."""
        track_ticket_operation("test_op", "success")
        metrics = get_metrics()
        assert b"ticket_operations_total" in metrics

    def test_get_metrics_contains_active_requests_gauge(self) -> None:
        """Test that metrics includes active requests gauge."""
        metrics = get_metrics()
        assert b"http_requests_active" in metrics

    def test_get_metrics_contains_success_counter(self) -> None:
        """Test that metrics includes success request counter."""
        metrics = get_metrics()
        assert b"http_requests_success_total" in metrics

    def test_get_metrics_contains_failure_counter(self) -> None:
        """Test that metrics includes failure request counter."""
        metrics = get_metrics()
        assert b"http_requests_failure_total" in metrics
