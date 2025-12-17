# Multi-stage Dockerfile for Ticket Bot Application
# Optimized for production deployment with minimal image size

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY external/ ./external/

# Install all dependencies in a virtual environment
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

WORKDIR /app

# Copy only the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ./src/
COPY external/ ./external/
COPY pyproject.toml ./

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port for Cloud Run (8080 is default)
EXPOSE 8080

# Run the main application
CMD ["python", "-m", "uvicorn", "ticket_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
