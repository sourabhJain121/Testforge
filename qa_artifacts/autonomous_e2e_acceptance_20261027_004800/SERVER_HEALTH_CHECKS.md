# TestForge — Server Health Checks & Baseline Endpoints

**Date:** 2026-10-27 00:53:00 IST  
**Service:** TestForge FastAPI ASGI Server  
**Endpoint:** `http://127.0.0.1:8000`  
**PID:** 17886  

---

## 1. Health & Readiness Verification

### `GET /readyz`
- **HTTP Status:** `200 OK`
- **Response Time:** 2.1 ms
- **Response Payload:**
  ```json
  {
    "status": "ready",
    "service": "testforge-backend",
    "subsystems": {
      "ast_mutator": "operational",
      "blackboard": "operational",
      "sandbox_storage": "operational",
      "sqlite_persistence": "operational"
    },
    "timestamp": 1793042553.154418
  }
  ```
- **Evaluation:** Subsystems initialized with zero errors.

### `GET /api/status`
- **HTTP Status:** `200 OK`
- **Response Payload:**
  ```json
  {
    "status": "operational",
    "service": "TestForge Engine",
    "version": "2.0.0",
    "accelerator": "Apple Silicon (NE/GPU) - MPS/MLX Accelerated",
    "active_jobs": 0,
    "completed_jobs": 0,
    "blackboard_revisions": 0
  }
  ```
- **Evaluation:** Hardware acceleration recognized, zero active job contention.

### `GET /api/mcp/status`
- **HTTP Status:** `200 OK`
- **Response Payload:**
  ```json
  {
    "status": "operational",
    "protocol": "Model Context Protocol (MCP)",
    "sdk": "FastMCP / mcp-python v1.28.0",
    "transport": "stdio JSON-RPC 2.0",
    "servers": [
      {
        "server_id": "testforge-filesystem",
        "status": "configured",
        "confinement": "samples_dir",
        "tools_count": 3
      },
      {
        "server_id": "testforge-github",
        "status": "configured",
        "auth_mode": "anonymous_rate_limited",
        "tools_count": 1
      }
    ],
    "total_tools_registered": 4
  }
  ```
- **Evaluation:** Both MCP tool servers operational over stdio JSON-RPC 2.0.

### `GET /.well-known/agent.json` (A2A AgentCard)
- **HTTP Status:** `200 OK`
- **Content-Type:** `application/json`
- **Evaluation:** Returns valid official A2A v0.3.0 schema with skills and capabilities.

---

## 2. Asset Integrity & HTTP Pipeline

| Resource | Method | Path | Status | Size | Evaluation |
|---|---|---|---|---|---|
| Single-Page UI | GET | `/` | 200 | 63,911 B | Clean render, no SSR errors |
| Main Script | GET | `/static/app.js` | 200 | 161,008 B | Full ES6 client loaded |
| Stylesheet | GET | `/static/style.css` | 200 | 51,209 B | Design system & glassmorphism |
| Built-in Samples | GET | `/api/samples` | 200 | 124 B | Sample fixtures available |
| Historical Benchmark | GET | `/api/benchmark/results`| 200 | 853 B | Verified benchmarks accessible |
