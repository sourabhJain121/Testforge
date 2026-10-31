# 07 — Frontend and Server Architecture Status Report

**Audit Timestamp:** `2026-10-30T18:12:20+05:30`  
**Host:** `127.0.0.1`  
**Active Architecture:** FastAPI + HTML5 / CSS3 / Vanilla JavaScript (Port 8000)  
**Decommissioned Stack:** Streamlit (Port 8501)

---

## 1. Port Verification

| Port | Bound Service | Process / PID | HTTP Status | Status Evaluation |
| :--- | :--- | :--- | :--- | :--- |
| **8000** | FastAPI (`server:app`) | Python (PID `21532`) | **HTTP 200 OK** | **ACTIVE & HEALTHY** |
| **8501** | Streamlit (`app.py`) | *None* | Connection Refused | **DISABLED / DECOMMISSIONED** |

### Network Inspection Evidence (`lsof -i :8000 -i :8501`)
```text
COMMAND     PID    USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
Python    21532 sourabh   10u  IPv4 0x8f7df0f8e9a1db78      0t0  TCP localhost:irdmi (LISTEN)
Python    21532 sourabh   17u  IPv4 0x5184d19cf11cdc8e      0t0  TCP localhost:irdmi->localhost:49358 (ESTABLISHED)
Google    34458 sourabh   31u  IPv4 0xe34c809c11aae914      0t0  TCP localhost:49358->localhost:irdmi (ESTABLISHED)
```
*(Note: Port 8000 maps to `irdmi` in macOS `/etc/services`)*

---

## 2. Endpoint Verification

### A. Dashboard UI (`GET http://127.0.0.1:8000/`)
- **HTTP Status:** `200 OK`
- **Content-Type:** `text/html; charset=utf-8`
- **Title:** `TestForge — Autonomous Agentic Test Hardening`
- **Assets Loaded:** `/static/style.css`, Google Fonts (`Inter`, `JetBrains Mono`, `Outfit`), Dynamic WebSocket connection for real-time lifecycle monitoring.

### B. Health Endpoint (`GET http://127.0.0.1:8000/healthz`)
- **HTTP Status:** `200 OK`
- **Response Payload:**
  ```json
  {
    "status": "healthy",
    "service": "testforge-backend",
    "version": "2.0.0",
    "timestamp": 1793363946.1461198
  }
  ```

### C. A2A AgentCard Endpoint (`GET http://127.0.0.1:8000/.well-known/agent.json`)
- **HTTP Status:** `200 OK`
- **Response Payload:**
  ```json
  {
    "capabilities": {
      "pushNotifications": false,
      "streaming": false
    },
    "defaultInputModes": ["text", "json"],
    "defaultOutputModes": ["text", "json"],
    "description": "Autonomous Agentic Unit Test Hardening System powered by Google ADK and CrewAI.",
    "name": "testforge-agent-system",
    "preferredTransport": "JSONRPC",
    "protocolVersion": "0.3.0",
    "provider": {
      "organization": "TestForge Autonomous Systems",
      "url": "https://github.com/sourabhJain121/Testforge"
    },
    "skills": [
      {
        "description": "Generates syntactically valid Python unit tests targeting surviving mutants using Google ADK.",
        "id": "unit-test-generation",
        "name": "Unit Test Generation",
        "tags": ["testing", "adk", "generation", "python"]
      },
      {
        "description": "Performs adversarial critique of test suites and surviving mutation diffs using CrewAI.",
        "id": "mutation-critique",
        "name": "Mutation Critique",
        "tags": ["critique", "crewai", "mutation-testing"]
      },
      {
        "description": "Executes a complete generator-critic hardening cycle updating the typed Blackboard.",
        "id": "hardening-workflow",
        "name": "Hardening Workflow",
        "tags": ["hardening", "workflow", "blackboard"]
      }
    ],
    "url": "http://127.0.0.1:8000/",
    "version": "1.0.0"
  }
  ```

---

## 3. Explanation of the User's Screenshot on Port 8501

In the screenshot provided by the user, the browser was pointing to `http://127.0.0.1:8501/`. Because Streamlit was explicitly disabled per the single-frontend mandate:
- Port 8501 is closed and returning connection refused (`curl: (7) Failed to connect to server`).
- Google Chrome displays a cached service-worker skeleton placeholder with dark gray layout blocks.
- The browser command `open http://127.0.0.1:8000/` was executed to redirect focus to the active, live FastAPI dashboard.

