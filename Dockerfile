# ── Production Dockerfile for QuantLib Pro ───────────────────────────────────
# Multi-stage build for optimized image size and security

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System dependencies for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Build wheels for all dependencies
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="QuantLib Pro Team"
LABEL version="1.0.0"
LABEL description="Production deployment of QuantLib Pro - Enterprise Quantitative Finance Platform"

# Security: Create non-root user early
RUN groupadd -r quantlib && useradd -r -g quantlib -u 1000 quantlib

WORKDIR /app

# Install runtime dependencies only (smaller image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    liblapack3 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy and install pre-built wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links /wheels /wheels/*.whl && \
    rm -rf /wheels /root/.cache

# Copy application code
COPY --chown=quantlib:quantlib quantlib_pro/ ./quantlib_pro/
COPY --chown=quantlib:quantlib pages/ ./pages/
COPY --chown=quantlib:quantlib QuantLib_Pro.py ./
COPY --chown=quantlib:quantlib .streamlit/ ./.streamlit/

# Create necessary directories with proper permissions
RUN mkdir -p data/cache data/logs data/backups data/uat && \
    chown -R quantlib:quantlib /app

# Switch to non-root user
USER quantlib

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose Streamlit port
EXPOSE 8501

# Environment variables for production
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_RUN_ON_SAVE=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Run Streamlit application
CMD ["streamlit", "run", "QuantLib_Pro.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
