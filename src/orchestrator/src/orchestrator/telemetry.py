"""Telemetry and observability for the Orchestrator Service.

This module provides Prometheus metrics for monitoring:
- Request latency
- Success/failure rates
- Request counts by endpoint and status
- AI provider usage
- Ticket operation metrics
"""

import re
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# ============================================================================
# CONSTANTS
# ============================================================================

HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 300
HTTP_ERROR_MIN = 400
HTTP_SERVER_ERROR = 500

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Request duration histogram (latency tracking)
request_duration_seconds = Histogram(
    "orchestrator_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Request counter (success/failure tracking)
request_count = Counter(
    "orchestrator_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Success rate counter
request_success_total = Counter(
    "orchestrator_requests_success_total",
    "Total successful HTTP requests (2xx status codes)",
    ["method", "endpoint"],
)

# Failure rate counter
request_failure_total = Counter(
    "orchestrator_requests_failure_total",
    "Total failed HTTP requests (4xx, 5xx status codes)",
    ["method", "endpoint", "status_code"],
)

# Active requests gauge
active_requests = Gauge(
    "orchestrator_requests_active",
    "Number of active HTTP requests",
    ["method", "endpoint"],
)

# AI provider metrics
ai_requests_total = Counter(
    "orchestrator_ai_requests_total",
    "Total AI provider requests",
    ["provider", "status"],
)

ai_request_duration_seconds = Histogram(
    "orchestrator_ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# Ticket operation metrics
ticket_operations_total = Counter(
    "orchestrator_ticket_operations_total",
    "Total ticket operations",
    ["operation", "status"],
)


# ============================================================================
# MIDDLEWARE
# ============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all HTTP requests."""

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path to reduce label cardinality."""
        # Match UUID patterns
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        normalized = re.sub(uuid_pattern, "{id}", path, flags=re.IGNORECASE)
        # Replace numeric IDs
        return re.sub(r"/\d+(?=/|$)", "/{id}", normalized)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            metrics_response: Response = await call_next(request)
            return metrics_response

        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        # Track active requests
        active_requests.labels(method=method, endpoint=endpoint).inc()

        # Track request duration
        start_time = time.time()

        try:
            response: Response = await call_next(request)
            status_code = response.status_code

            # Record metrics
            duration = time.time() - start_time
            request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).observe(duration)

            request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

            # Track success/failure
            if HTTP_SUCCESS_MIN <= status_code < HTTP_SUCCESS_MAX:
                request_success_total.labels(method=method, endpoint=endpoint).inc()
            elif status_code >= HTTP_ERROR_MIN:
                request_failure_total.labels(
                    method=method, endpoint=endpoint, status_code=status_code
                ).inc()
        except Exception:
            # Track exceptions as failures
            duration = time.time() - start_time
            request_duration_seconds.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).observe(duration)

            request_count.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).inc()
            request_failure_total.labels(
                method=method, endpoint=endpoint, status_code=HTTP_SERVER_ERROR
            ).inc()

            raise
        else:
            return response

        finally:
            # Decrement active requests
            active_requests.labels(method=method, endpoint=endpoint).dec()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def track_ai_request(provider: str, status: str = "success", duration: float | None = None) -> None:
    """Track an AI provider request."""
    ai_requests_total.labels(provider=provider, status=status).inc()
    if duration is not None:
        ai_request_duration_seconds.labels(provider=provider).observe(duration)


def track_ticket_operation(operation: str, status: str = "success") -> None:
    """Track a ticket operation."""
    ticket_operations_total.labels(operation=operation, status=status).inc()


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    result = generate_latest()
    assert isinstance(result, bytes)
    return result
