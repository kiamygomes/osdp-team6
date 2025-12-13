# Telemetry and Observability

## Overview

The Ticket Service includes comprehensive telemetry using Prometheus metrics to monitor application health, performance, and reliability.

## Metrics Endpoint

Access metrics at: `GET /metrics`

This endpoint exposes metrics in Prometheus format that can be scraped by monitoring systems.

## Available Metrics

### Request Latency
- **Metric**: `http_request_duration_seconds`
- **Type**: Histogram
- **Labels**: `method`, `endpoint`, `status_code`
- **Description**: Tracks HTTP request latency in seconds
- **Buckets**: 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s

### Request Count
- **Metric**: `http_requests_total`
- **Type**: Counter
- **Labels**: `method`, `endpoint`, `status_code`
- **Description**: Total number of HTTP requests

### Success Rate
- **Metric**: `http_requests_success_total`
- **Type**: Counter
- **Labels**: `method`, `endpoint`
- **Description**: Total successful requests (2xx status codes)

### Failure Rate
- **Metric**: `http_requests_failure_total`
- **Type**: Counter
- **Labels**: `method`, `endpoint`, `status_code`
- **Description**: Total failed requests (4xx, 5xx status codes)

### Active Requests
- **Metric**: `http_requests_active`
- **Type**: Gauge
- **Labels**: `method`, `endpoint`
- **Description**: Number of currently active HTTP requests

### Ticket Operations
- **Metric**: `ticket_operations_total`
- **Type**: Counter
- **Labels**: `operation`, `status`
- **Description**: Total ticket operations (create, update, delete, etc.)

- **Metric**: `ticket_operation_duration_seconds`
- **Type**: Histogram
- **Labels**: `operation`
- **Description**: Duration of ticket operations

## Integration with Monitoring Platforms

### Prometheus
Add this scrape config to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ticket-service'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana
Import the provided dashboard (see `grafana-dashboard.json`) or create custom dashboards using these queries:

**Request Latency (p95)**:
```promql
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket[5m])
)
```

**Success Rate**:
```promql
rate(http_requests_success_total[5m]) / 
rate(http_requests_total[5m]) * 100
```

**Error Rate**:
```promql
rate(http_requests_failure_total[5m]) / 
rate(http_requests_total[5m]) * 100
```

### Render.com (Deployment Platform)
Render automatically scrapes the `/metrics` endpoint if you enable metrics in your service settings.

## Example Queries

### Average Request Latency by Endpoint
```promql
rate(http_request_duration_seconds_sum[5m]) / 
rate(http_request_duration_seconds_count[5m])
```

### Requests Per Second
```promql
rate(http_requests_total[1m])
```

### Error Rate Percentage
```promql
sum(rate(http_requests_failure_total[5m])) / 
sum(rate(http_requests_total[5m])) * 100
```

### Active Ticket Operations
```promql
sum(http_requests_active{endpoint=~"/api/v1/tickets.*"})
```

## Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: ticket_service
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_failure_total[5m])) / 
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        annotations:
          summary: "High request latency"
          description: "P95 latency is {{ $value }}s"
```

## Local Testing

1. Start the service:
   ```bash
   uvicorn ticket_service.main:app --reload
   ```

2. Generate some traffic:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/tickets
   ```

3. View metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

## Production Deployment

The telemetry is automatically enabled in production. Metrics are exposed at the `/metrics` endpoint and can be scraped by:

- Prometheus
- Datadog
- New Relic
- Grafana Cloud
- Any Prometheus-compatible monitoring system

## Performance Impact

The telemetry middleware adds minimal overhead:
- ~0.1-0.5ms per request
- Negligible memory footprint
- Metrics are stored in-memory and reset on restart
- No external dependencies required
