# Monitoring and Observability

This document describes the monitoring and observability features implemented in the OSDP Ticket Bot system.

## Overview

The application emits telemetry data for key operations using Prometheus metrics. This enables real-time monitoring of:

- **Request Latency**: How long requests take to process
- **Success Rate**: Percentage of successful requests (2xx status codes)
- **Failure Rate**: Percentage of failed requests (4xx, 5xx status codes)
- **Active Requests**: Number of currently processing requests
- **Ticket Operations**: Counts of ticket operations by type and status
- **AI Provider Usage**: Metrics for AI provider requests and latency

## Instrumentation

### Ticket Service Metrics

The Ticket Service (`src/ticket_service`) exposes the following metrics at `/metrics`:

#### Request Latency
```
http_request_duration_seconds_bucket{method="POST",endpoint="/api/v1/tickets",status_code="201",le="0.1"} 45
http_request_duration_seconds_sum{method="POST",endpoint="/api/v1/tickets",status_code="201"} 3.2
http_request_duration_seconds_count{method="POST",endpoint="/api/v1/tickets",status_code="201"} 50
```

#### Success Rate
```
http_requests_success_total{method="GET",endpoint="/api/v1/tickets"} 150
http_requests_success_total{method="POST",endpoint="/api/v1/tickets"} 50
```

#### Failure Rate
```
http_requests_failure_total{method="GET",endpoint="/api/v1/tickets/{id}",status_code="404"} 5
http_requests_failure_total{method="POST",endpoint="/api/v1/tickets",status_code="400"} 3
```

#### Active Requests
```
http_requests_active{method="GET",endpoint="/api/v1/tickets"} 2
```

#### Ticket Operations
```
ticket_operations_total{operation="create",status="success"} 50
ticket_operations_total{operation="update",status="success"} 30
ticket_operations_total{operation="delete",status="success"} 10
```

### Orchestrator Service Metrics

The Orchestrator Service (`src/orchestrator`) exposes similar metrics at `/metrics`:

#### Request Latency
```
orchestrator_request_duration_seconds_bucket{method="POST",endpoint="/process",status_code="200",le="1.0"} 80
orchestrator_request_duration_seconds_sum{method="POST",endpoint="/process",status_code="200"} 45.6
orchestrator_request_duration_seconds_count{method="POST",endpoint="/process",status_code="200"} 100
```

#### AI Provider Metrics
```
orchestrator_ai_requests_total{provider="claude",status="success"} 75
orchestrator_ai_requests_total{provider="openai",status="success"} 25
orchestrator_ai_request_duration_seconds_sum{provider="claude"} 120.5
orchestrator_ai_request_duration_seconds_count{provider="claude"} 75
```

## Accessing Metrics

### Local Development

1. Start the service:
   ```bash
   # Ticket Service
   uvicorn ticket_service.main:app --reload --port 8000
   
   # Orchestrator Service
   uvicorn orchestrator.orchestrator_service:app --reload --port 8080
   ```

2. Access metrics endpoints:
   - Ticket Service: http://localhost:8000/metrics
   - Orchestrator Service: http://localhost:8080/metrics

### Production (Render)

Metrics are exposed at:
- Ticket Service: https://ticket-service.onrender.com/metrics
- Orchestrator Service: https://orchestrator.onrender.com/metrics

## Visualization

### Prometheus Configuration

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ticket-service'
    scrape_interval: 15s
    static_configs:
      - targets: ['ticket-service.onrender.com:443']
    scheme: https
    metrics_path: /metrics

  - job_name: 'orchestrator-service'
    scrape_interval: 15s
    static_configs:
      - targets: ['orchestrator.onrender.com:443']
    scheme: https
    metrics_path: /metrics
```

### Grafana Dashboards

#### Request Latency Dashboard

Query for average request latency:
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

Query for 95th percentile latency:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Success Rate Dashboard

Query for success rate percentage:
```promql
100 * sum(rate(http_requests_success_total[5m])) / sum(rate(http_requests_total[5m]))
```

#### Failure Rate Dashboard

Query for failure rate percentage:
```promql
100 * sum(rate(http_requests_failure_total[5m])) / sum(rate(http_requests_total[5m]))
```

#### Active Requests Dashboard

Query for current active requests:
```promql
http_requests_active
```

### Example Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "OSDP Ticket Bot Monitoring",
    "panels": [
      {
        "title": "Request Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Success Rate",
        "targets": [
          {
            "expr": "100 * sum(rate(http_requests_success_total[5m])) / sum(rate(http_requests_total[5m]))"
          }
        ]
      },
      {
        "title": "Failure Rate",
        "targets": [
          {
            "expr": "100 * sum(rate(http_requests_failure_total[5m])) / sum(rate(http_requests_total[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Monitoring Platform Integration

### Datadog

To integrate with Datadog:

1. Install Datadog agent on your server
2. Configure Prometheus integration in Datadog
3. Add the metrics endpoints to Datadog's scrape configuration

### CloudWatch

For AWS CloudWatch integration:

1. Use CloudWatch agent with Prometheus scraping
2. Configure the agent to scrape metrics endpoints
3. Create CloudWatch dashboards using the collected metrics

### Prometheus + Grafana (Recommended)

1. Deploy Prometheus to scrape metrics
2. Deploy Grafana for visualization
3. Import the provided dashboard JSON
4. Set up alerts for critical metrics

## Alerts

### Recommended Alert Rules

```yaml
groups:
  - name: ticket_service_alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "High request latency detected"
          
      - alert: HighFailureRate
        expr: 100 * sum(rate(http_requests_failure_total[5m])) / sum(rate(http_requests_total[5m])) > 5
        for: 5m
        annotations:
          summary: "High failure rate detected"
          
      - alert: ServiceDown
        expr: up{job="ticket-service"} == 0
        for: 1m
        annotations:
          summary: "Ticket service is down"
```

## Testing Metrics

### Manual Testing

1. Make requests to the service:
   ```bash
   curl -X POST http://localhost:8000/api/v1/tickets \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test-user" \
     -H "X-Project-Key: TEST" \
     -d '{"title":"Test","description":"Test","reporter":"user@example.com","priority":"high"}'
   ```

2. Check metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

3. Verify metrics are updated

### Automated Testing

Integration tests verify metrics collection:

```python
def test_metrics_track_requests():
    """Test that metrics are collected for requests."""
    client.post("/api/v1/tickets", json={...})
    
    metrics_response = client.get("/metrics")
    assert "http_requests_total" in metrics_response.text
    assert "http_request_duration_seconds" in metrics_response.text
```

## Evidence

### Metrics Endpoint Screenshot

The metrics endpoint is accessible and returns Prometheus-formatted metrics:

```
# HELP http_request_duration_seconds HTTP request latency in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/health",status_code="200",le="0.005"} 150.0
http_request_duration_seconds_bucket{method="GET",endpoint="/health",status_code="200",le="0.01"} 150.0
...
http_request_duration_seconds_sum{method="GET",endpoint="/health",status_code="200"} 0.45
http_request_duration_seconds_count{method="GET",endpoint="/health",status_code="200"} 150.0

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health",status_code="200"} 150.0
http_requests_total{method="POST",endpoint="/api/v1/tickets",status_code="201"} 50.0

# HELP http_requests_success_total Total successful HTTP requests (2xx status codes)
# TYPE http_requests_success_total counter
http_requests_success_total{method="GET",endpoint="/health"} 150.0
http_requests_success_total{method="POST",endpoint="/api/v1/tickets"} 50.0

# HELP http_requests_failure_total Total failed HTTP requests (4xx, 5xx status codes)
# TYPE http_requests_failure_total counter
http_requests_failure_total{method="GET",endpoint="/api/v1/tickets/{id}",status_code="404"} 5.0
```

### Test Results

All monitoring tests pass in CI/CD:

- ✅ Metrics endpoint accessible
- ✅ Request latency tracked
- ✅ Success rate tracked
- ✅ Failure rate tracked
- ✅ Active requests tracked
- ✅ Ticket operations tracked

See CircleCI test results for detailed evidence.

## Maintenance

### Adding New Metrics

1. Define metric in `telemetry.py`:
   ```python
   new_metric = Counter(
       "new_metric_total",
       "Description of new metric",
       ["label1", "label2"],
   )
   ```

2. Track metric in code:
   ```python
   new_metric.labels(label1="value1", label2="value2").inc()
   ```

3. Add tests for new metric
4. Update documentation

### Metric Retention

- Prometheus default retention: 15 days
- For longer retention, configure Prometheus with `--storage.tsdb.retention.time` flag
- Consider using remote storage (e.g., Thanos, Cortex) for long-term retention

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
