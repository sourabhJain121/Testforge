# ==============================================================================
# TestForge: Autonomous Agentic Unit Test Hardening System
# Production Multi-Stage Container Definition (Python 3.13)
# Optimized for Google Cloud Run (Serverless Container) & Render
# ==============================================================================

FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080

# Install essential OS runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up dedicated non-root application user
RUN groupadd -r testforge && useradd -r -g testforge -m -d /home/testforge testforge

WORKDIR /app

# Install project dependencies cleanly from pyproject.toml and requirements.txt
COPY pyproject.toml requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into container
COPY . /app/

# Install testforge package in editable mode from pyproject.toml without re-downloading deps
RUN pip install --no-cache-dir --no-deps -e .

# Set up writable directories and permissions for non-root execution
# Ensures SQLite WAL (testforge_blackboard.db) and subprocess sandboxes work without PermissionError
RUN mkdir -p /app/qa_artifacts /tmp/testforge \
    && chown -R testforge:testforge /app /home/testforge /tmp/testforge \
    && chmod -R 777 /tmp \
    && chmod -R u+rwx /app

# Switch to non-root user
USER testforge

# Expose dynamic Cloud Run (8080), local dev (8000), and dashboard (8501) ports
EXPOSE 8000
EXPOSE 8080
EXPOSE 8501

# Container healthcheck targeting standard healthz probe
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/healthz || exit 1

# Default entrypoint: Start FastAPI server respecting dynamic $PORT
CMD exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}
