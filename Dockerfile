# ==============================================================================
# CloudOps Enterprise Platform - Multi-Stage Production Dockerfile
# Security Best Practice: Multi-stage, minimal runtime, non-root user execution
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Minimal Hardened Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Security: Create dedicated non-root user & group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -m appuser

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# Configure runtime environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# Copy application code with non-root ownership
COPY --chown=appuser:appgroup src /app/src

# Drop privileges to non-root user
USER 10001:10001

EXPOSE 8000

# Container liveness health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1

# Launch ASGI application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
