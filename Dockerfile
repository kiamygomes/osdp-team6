# Multi-stage Dockerfile for Ticket Bot Application
# Optimized for production deployment with minimal image size

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock* ./

# Copy workspace member pyproject.toml files (needed for workspace resolution)
COPY src/ ./src/
COPY external/ ./external/

# Install production dependencies in a virtual environment
# Install the ticket-service workspace member specifically
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache ./src/ticket_service

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/external ./external
COPY pyproject.toml ./

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src:/app"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check - verify the service is responsive
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=2.0)" || exit 1

# Expose port for Cloud Run (8080 is default)
EXPOSE 8080

# Run the ticket service FastAPI application
CMD ["python", "-m", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0", "--port", "8080"]