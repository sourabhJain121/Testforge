# ==============================================================================
# TestForge: Autonomous Agentic Unit Test Hardening System
# Production Multi-Stage Container Definition (Python 3.13)
# ==============================================================================

FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install essential OS runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up dedicated non-root application user
RUN groupadd -r testforge && useradd -r -g testforge -m -d /home/testforge testforge

WORKDIR /app

# Install project dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files and change ownership
COPY . /app/
RUN chown -R testforge:testforge /app

# Switch to non-root user
USER testforge

# Expose FastAPI backend (8000) and Streamlit dashboard (8501)
EXPOSE 8000 8501

# Container healthcheck targeting standard healthz probe
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Default entrypoint: Start FastAPI server
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
