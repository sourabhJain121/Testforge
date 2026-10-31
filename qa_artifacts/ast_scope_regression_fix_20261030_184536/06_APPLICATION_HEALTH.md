# 06 — Application Health & Architecture Status

**Audit & Fix Timestamp:** `2026-10-30T18:45:36+05:30`  
**Host:** `127.0.0.1`  
**Active Architecture:** FastAPI + HTML5/CSS/JavaScript (Port 8000)  
**Decommissioned Stack:** Streamlit (Port 8501)

---

## 1. Network & Process Verification

| Port | Service | Process / PID | HTTP Status | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **8000** | FastAPI (`server:app`) | Python (PID `21532`) | **HTTP 200 OK** | **ACTIVE & HEALTHY** |
| **8501** | Streamlit (`app.py`) | *None* | Connection Refused | **DISABLED / INACTIVE** |

### Network Inspection Evidence (`lsof -i :8000 -i :8501`)
```text
COMMAND     PID    USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
Python    21532 sourabh   10u  IPv4 0x8f7df0f8e9a1db78      0t0  TCP localhost:irdmi (LISTEN)
Python    21532 sourabh   17u  IPv4 0x5184d19cf11cdc8e      0t0  TCP localhost:irdmi->localhost:49358 (ESTABLISHED)
```

---

## 2. Live HTTP Endpoint Verification

### A. Health Endpoint (`GET http://127.0.0.1:8000/healthz`)
- **HTTP Status:** `200 OK`
- **Response Payload:**
  ```json
  {
    "status": "healthy",
    "service": "testforge-backend",
    "version": "2.0.0",
    "timestamp": 1793365774.352695
  }
  ```

### B. A2A Protocol AgentCard (`GET http://127.0.0.1:8000/.well-known/agent.json`)
- **HTTP Status:** `200 OK`
- **Verified Fields:**
  - `name`: `"testforge-agent-system"`
  - `protocolVersion`: `"0.3.0"`
  - `skills`: `["unit-test-generation", "mutation-critique", "hardening-workflow"]`

### C. Static Asset Delivery (`GET http://127.0.0.1:8000/static/style.css`)
- **HTTP Status:** `200 OK`
- **Content-Type:** `text/css; charset=utf-8`

### D. Port 8501 Decommissioning Check
```bash
curl -s http://127.0.0.1:8501/
# Output: Port 8501 is closed as expected.
```
Streamlit was not started. Port 8501 remains completely offline.

