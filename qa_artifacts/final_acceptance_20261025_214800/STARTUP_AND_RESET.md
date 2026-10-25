# TESTFORGE — APPLICATION STARTUP, REPRODUCTION & RESET PROCEDURE

This guide details how to launch the backend, access the frontend, rerun automated browser regression suites, and reset the platform to a pristine state.

---

## 1. Environment & Prerequisites

- **Python Environment:** `.venv-release` (Python 3.13.17)
- **Dependencies:** All dependencies pre-installed in `.venv-release` (`fastapi`, `uvicorn`, `crewai`, `google-genai`, `mcp`, `pytest`, `websockets`, `requests`).
- **Operating System:** macOS arm64 / Linux

---

## 2. Starting the Application

### Standard Local Launch (Backend + Frontend)
FastAPI serves the API and the static frontend simultaneously on port 8000:

```bash
cd /Users/sourabh/TestForge
.venv-release/bin/python server.py
```

- **Frontend URL:** `http://127.0.0.1:8000/`
- **Health Endpoint:** `http://127.0.0.1:8000/healthz`
- **Readiness Endpoint:** `http://127.0.0.1:8000/api/ready`
- **A2A Agent Card:** `http://127.0.0.1:8000/.well-known/agent-card.json`
- **MCP Tool Status:** `http://127.0.0.1:8000/api/mcp/status`
- **Blackboard Checkpoints API:** `http://127.0.0.1:8000/api/checkpoints`

---

## 3. Running Automated Test Suites

### 3.1 Run Full Backend Test Suite
```bash
cd /Users/sourabh/TestForge
.venv-release/bin/pytest tests/ -q
```
*Expected Outcome:* 395 passed tests, Exit Code 0.

### 3.2 Run 11 Teacher Requirements Acceptance Suite
```bash
cd /Users/sourabh/TestForge
.venv-release/bin/pytest tests/test_blackboard.py tests/test_mcp.py tests/test_crew_critic.py tests/test_blast_and_adk.py tests/test_a2a.py tests/test_security.py tests/test_observability.py tests/test_benchmarking.py tests/test_deployment.py -q
```
*Expected Outcome:* 123 passed tests, Exit Code 0.

### 3.3 Run End-to-End Browser Regression Audit
Ensure the server is running on `http://127.0.0.1:8000`, then execute:
```bash
cd /Users/sourabh/TestForge
.venv-release/bin/python qa_artifacts/final_acceptance_20261025_214800/run_full_acceptance_audit.py
```
*Expected Outcome:* 30 actionable controls exercised across 9 tabs and 4 modals, 17 screenshots captured, Exit Code 0.

---

## 4. Platform Reset Procedure

To restore TestForge to an empty demonstration state without destroying code:

1. **Stop Server Process:**
   ```bash
   lsof -ti :8000 | xargs kill -9 2>/dev/null || true
   ```
2. **Clear Checkpoint SQLite Database & Traces:**
   ```bash
   rm -f testforge_blackboard.db testforge_blackboard.db-wal testforge_blackboard.db-shm
   rm -f testforge_trace.jsonl
   ```
3. **Restart Clean Server:**
   ```bash
   .venv-release/bin/python server.py
   ```
   *The database schema will automatically re-initialize cleanly on startup.*
