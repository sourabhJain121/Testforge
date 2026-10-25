# TestForge Production Deployment & Operations Guide

## Overview

TestForge is an autonomous agentic unit test hardening system integrating Google ADK, CrewAI, A2A Protocol (v0.3.0), FastMCP tools, and a typed Blackboard architecture.

This guide provides reproducible procedures for local execution, containerized multi-service deployment, health check monitoring, and operational troubleshooting.

---

## Architecture Topology

```
                         [ External A2A Clients / Web Browsers ]
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 │                                                 │
          Port 8000: FastAPI Backend                     Port 8501: Streamlit
                 │                                                 │
   ┌─────────────┼────────────────────────┐                        │
   │             │                        │                        │
[Healthz]    [Readyz]   [AgentCard]  [A2A Handler]                 │
 (/healthz)  (/readyz)  (/.well-known/ (JSON-RPC)                  │
                          agent-card.json)                         │
                 │                                                 │
         [A2A Broker & Blackboard]                                 │
                 │                                                 │
     ┌───────────┴───────────┐                                     │
     ▼                       ▼                                     │
[Google ADK Generator]  [CrewAI Critic]                            │
     │                       │                                     │
     └───────────┬───────────┘                                     │
                 ▼                                                 ▼
        [Parallel Sandbox Runner]                      [Interactive Telemetry UI]
        (Isolated Subprocesses)                        (Real-time Iteration State)
```

---

## Services & Port Allocations

| Service | Port | Protocol | Description | Health Endpoint |
|---|---|---|---|---|
| **FastAPI Backend** | `8000` | HTTP / JSON-RPC | REST API, A2A endpoint, sandbox orchestrator, telemetry | `GET /healthz`, `GET /readyz` |
| **Streamlit Dashboard** | `8501` | HTTP / WebSocket | Interactive mutation testing & reflection UI | Internal Streamlit health probe |

---

## Environment Variables & Configuration

Supply configuration via environment variables or a `.env` file. **Never commit secrets to source control.**

| Variable | Required? | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Optional | `""` | Google Gemini API key for Google ADK generator and LLM reflection |
| `OPENROUTER_API_KEY` | Optional | `""` | OpenRouter API key for third-party foundation models |
| `GITHUB_TOKEN` | Optional | `""` | GitHub Personal Access Token for GitHub MCP tool inspection |
| `TESTFORGE_API_URL` | Optional | `http://localhost:8000` | Backend API URL used by the frontend dashboard |
| `PYTHONUNBUFFERED` | Optional | `1` | Forces unbuffered stdout/stderr streams for container logging |

---

## Deployment Option 1: Native Local Deployment

### 1. Prerequisites
- Python 3.13 (or compatible isolated virtual environment).
- Git.

### 2. Startup Backend
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Startup Interactive Dashboard
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 4. Verify Local Health
```bash
# Liveness probe
curl -f http://localhost:8000/healthz

# Deep readiness probe (tests AST parser, blackboard, storage)
curl -f http://localhost:8000/readyz

# A2A Discovery
curl -f http://localhost:8000/.well-known/agent-card.json
```

---

## Deployment Option 2: Docker & Docker Compose

TestForge provides a multi-stage `Dockerfile` (based on `python:3.13-slim`) and a `docker-compose.yml` service specification.

### 1. Build and Start Services
```bash
# Build images and start backend + dashboard
docker compose up -d --build
```

### 2. Inspect Running Containers
```bash
docker compose ps
```
Expected output:
```
NAME                 COMMAND                  SERVICE     STATUS
testforge-backend    "python -m uvicorn s…"   backend     running (healthy)
testforge-dashboard  "streamlit run app.p…"   dashboard   running
```

### 3. Check Container Health Status
```bash
# Query Docker health check
docker inspect --format='{{json .State.Health}}' testforge-backend | jq .
```

### 4. View Aggregated Logs
```bash
docker compose logs -f
```

### 5. Tear Down
```bash
docker compose down -v
```

---

## Health Check Specifications

### 1. Liveness Probe (`GET /healthz`)
- **Purpose:** Verifies that the FastAPI process is alive and accepting connections.
- **Success Response:**
  ```json
  {
    "status": "healthy",
    "service": "testforge-backend",
    "version": "2.0.0",
    "timestamp": 1729584000.0
  }
  ```
- **Exit Code:** `200 OK`

### 2. Readiness Probe (`GET /readyz`)
- **Purpose:** Validates that all internal subsystems are operational before routing client traffic:
  - `ast_mutator`: Verifies Python AST fault injection is functioning.
  - `blackboard`: Verifies all 5 state partitions are initialized and thread-safe.
  - `sandbox_storage`: Verifies temporary directory write access for subprocess testing.
- **Success Response (`200 OK`):**
  ```json
  {
    "status": "ready",
    "service": "testforge-backend",
    "subsystems": {
      "ast_mutator": "operational",
      "blackboard": "operational",
      "sandbox_storage": "operational"
    },
    "timestamp": 1729584000.0
  }
  ```
- **Degraded Response (`503 Service Unavailable`):**
  If any subsystem fails to initialize, the status code changes to 503 and the affected component is detailed.

---

## Troubleshooting Guide

| Symptom | Root Cause | Remediation |
|---|---|---|
| `503 Service Unavailable` on `/readyz` | Subsystem degraded (e.g. read-only filesystem) | Check filesystem write permissions in `/tmp` and ensure `ast_mutator` parses cleanly. |
| `Cannot connect to Docker daemon` | Docker Desktop / dockerd not running on host | Start Docker Desktop application or execute services via native Python 3.13 virtualenv. |
| Tests fail with `SecurityRefusal` | Malicious input prompt or dangerous AST detected | Check the code being ingested. System deliberately refuses `eval`, `os.system`, or prompt overrides. |
| Model failover to `Deterministic AST Fallback` | `GEMINI_API_KEY` missing or invalid | Supply valid `GEMINI_API_KEY` or rely on deterministic AST test generation for offline runs. |
