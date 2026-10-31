# TESTFORGE — SETUP, EXECUTION & TROUBLESHOOTING GUIDE
## Installation, Environment Configuration, Startup Commands, Pytest Execution & Diagnostic Playbook

**Document Version:** 2.0.0  
**Target Audience:** Operators, Evaluators, Developers  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/SETUP_EXECUTION_AND_TROUBLESHOOTING.md`

---

## 1. SYSTEM REQUIREMENTS & RUNTIME ENVIRONMENT

- **Operating System:** macOS (Apple Silicon arm64 / Intel x86_64) or Linux (Ubuntu 22.04+ / Debian 12+)
- **Python Version:** Python 3.13 (Verified under Python 3.13.18)
- **Active Environment Path:** `/Users/sourabh/TestForge/.venv-release`
- **Port Allocations:**
  - `8000` — FastAPI Backend & HTML/CSS/JS Single-Page Application (Required)
  - `8501` — Legacy Streamlit Port (**PERMANENTLY DISABLED & MUST REMAIN UNBOUND**)

---

## 2. INSTALLATION & ENVIRONMENT SETUP

### 2.1 Virtual Environment Activation
```bash
# Navigate to repository root
cd /Users/sourabh/TestForge

# Activate the production release virtual environment
source .venv-release/bin/activate

# Verify Python runtime version
python --version
# Expected: Python 3.13.x
```

### 2.2 Dependency Verification
If re-creating the environment from scratch:
```bash
python -m venv .venv-release
source .venv-release/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 3. STARTING THE APPLICATION

### Option A: Direct Uvicorn Launch (Recommended)
```bash
.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

### Option B: Using the Provided Shell Wrapper
```bash
chmod +x start_testforge.sh
./start_testforge.sh
```

### Option C: Containerized Deployment via Docker
```bash
# Build and run using Docker Compose
docker-compose up --build -d

# Verify container health
curl http://127.0.0.1:8000/healthz
```

---

## 4. ACCESSING THE APPLICATION

Once started, open any modern web browser (Chrome, Firefox, Safari, Edge):
- **Web User Interface (SPA):** [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/)
- **Swagger Interactive API Documentation:** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation:** [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)
- **A2A Agent Card:** [`http://127.0.0.1:8000/.well-known/agent-card.json`](http://127.0.0.1:8000/.well-known/agent-card.json)
- **Health Check Probe:** [`http://127.0.0.1:8000/healthz`](http://127.0.0.1:8000/healthz)

---

## 5. RUNNING THE VERIFICATION TEST SUITES

### 5.1 Complete Regression Suite (523 Tests)
```bash
.venv-release/bin/python -m pytest tests/ -q
# Expected outcome: 523 passed in ~350s (Exit code 0)
```

### 5.2 Dedicated Security Regression Suite (84 Tests)
```bash
.venv-release/bin/python -m pytest tests/test_network_security.py tests/test_mcp_network_security.py tests/test_prompt_injection_defense.py -v
# Expected outcome: 84 passed in ~19s (Exit code 0)
```

### 5.3 Mutation-Guided Repair & Benchmark Suite
```bash
.venv-release/bin/python -m pytest tests/test_mutation_guided_repair.py tests/test_benchmarking.py -v
# Expected outcome: 51 passed in ~25s (Exit code 0)
```

### 5.4 Automated Frontend Edge-Case & Cancellation Test
```bash
.venv-release/bin/python qa_artifacts/final_phase2_execution/test_frontend_failure_handling.py
# Expected outcome: 8 / 8 failure & recovery scenarios passed
```

---

## 6. INSPECTING LOGS & CHECKPOINTS

### Inspect Active Telemetry Log
```bash
# View live JSONL event trace
tail -f testforge_trace.jsonl | jq .
```

### Inspect SQLite Checkpoints
```bash
# Query historical run records
sqlite3 qa_artifacts/testforge_checkpoints.db "SELECT checkpoint_id, target_file, mutation_score, timestamp FROM checkpoints ORDER BY timestamp DESC LIMIT 5;"
```

---

## 7. TROUBLESHOOTING & COMMON ISSUES

### Issue 1: Port 8000 is already in use
- **Symptom:** `OSError: [Errno 48] Address already in use`
- **Resolution:**
  ```bash
  # Find PID using port 8000
  lsof -i :8000
  # Terminate the rogue process
  kill -9 <PID>
  ```

### Issue 2: Streamlit port 8501 warning
- **Symptom:** Evaluator asks why Streamlit is not responding at `http://127.0.0.1:8501/`.
- **Explanation:** Streamlit was permanently retired and disabled. TestForge runs as a consolidated single-frontend architecture on FastAPI port `8000`.

### Issue 3: macOS arm64 PyO3 / AnyIO Warning
- **Symptom:** `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated...`
- **Explanation:** Benign deprecation warnings from upstream `starlette` / `crewai` library internals under Python 3.13. They do not impact test execution or runtime stability.

