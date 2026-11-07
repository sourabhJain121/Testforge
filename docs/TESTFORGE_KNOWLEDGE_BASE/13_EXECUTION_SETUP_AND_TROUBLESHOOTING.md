# TestForge — Execution, Setup & Troubleshooting Guide

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Primary Platform:** macOS (Darwin arm64) & Linux  
**Target Python Version:** Python 3.13 (or 3.10–3.12)  

---

## 1. System Prerequisites & Environment Setup

### 1.1 Prerequisites
- **Operating System:** macOS (Apple Silicon M1/M2/M3/M4 recommended for local Metal GPU acceleration) or Linux (x86_64 / aarch64).
- **Python Version:** Python 3.10, 3.11, 3.12, or 3.13 (Authoritative runtime: Python 3.13.18 in `.venv-release`).
- **RAM:** Minimum 8GB (16GB+ recommended if running 7B local Ollama models).
- **Disk Space:** ~2GB free space (includes SQLite checkpoints and Pytest virtual environment).

### 1.2 Virtual Environment Activation
```bash
# Navigate to repository root
cd /Users/sourabh/TestForge

# Activate the verified release virtual environment
source .venv-release/bin/activate

# Verify Python runtime and Pytest version
python --version   # Output: Python 3.13.18
pytest --version   # Output: pytest 9.1.1
```

---

## 2. Optional Local Ollama Setup (Tier 3 Local LLM)

If you wish to run TestForge completely offline with local open-weights models:

```bash
# 1. Install Ollama (via Homebrew on macOS)
brew install ollama

# 2. Start the Ollama background daemon
ollama serve > /dev/null 2>&1 &

# 3. Pull verified code models
ollama pull codellama:7b
ollama pull qwen2.5-coder:7b

# 4. Verify local models are running and available
curl -s http://127.0.0.1:11434/api/tags | python -m json.tool
```

---

## 3. Starting the TestForge Application Server

TestForge includes a startup script with automatic port checks, environment initialization, and checkpoint database verification:

```bash
# Start server using the release script
./start_testforge.sh

# Or start directly with Uvicorn
uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

Once running, access the web dashboard in Google Chrome or Safari:
- **Web Dashboard:** `http://127.0.0.1:8000/`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/healthz`
- **Readiness Check:** `http://127.0.0.1:8000/readyz`
- **A2A Agent Card:** `http://127.0.0.1:8000/.well-known/agent.json`

---

## 4. Running Verification & Evaluation Commands

### 1. Running the Full Regression Suite (611 Tests)
```bash
# Run complete test suite (expected 611 passed in ~378 seconds)
.venv-release/bin/python -m pytest tests/ -q
```

### 2. Running Dynamic Model Identification & Observability Tests
```bash
# Run dynamic model resolution and token accounting tests (20 tests)
.venv-release/bin/python -m pytest tests/test_dynamic_model_identification.py tests/test_token_observability_audit.py -v
```

### 3. Measuring TestForge Engine Statement Coverage
```bash
# Run statement coverage against the core engine (expected 81.33%)
.venv-release/bin/python -m pytest --cov=testforge --cov-report=term --cov-report=html tests/
```

### 4. Running Security Guardrail Evaluation (Criterion 8)
```bash
# Run the 18 security regression tests
.venv-release/bin/python -m pytest tests/test_security_variations.py -v

# Run the 120 deterministic security trials
.venv-release/bin/python -m testforge.security_evaluation_engine
```

### 5. Running End-to-End Performance Benchmarking (Criterion 10)
```bash
# Run performance evaluation harness (generates 60-run matrix)
.venv-release/bin/python -m testforge.performance_evaluator
```

### 6. Running Playwright Headless Browser Automation
```bash
# Run browser verification script to capture live screenshots
.venv-release/bin/python scripts/verify_browser_observability.py
```

---

## 5. Troubleshooting Common Issues

### Issue 1: Port 8000 Already in Use
- **Symptom:** `ERROR: [Errno 48] Address already in use`.
- **Cause:** A previous instance of `server.py` or `uvicorn` is running in the background.
- **Resolution:**
  ```bash
  lsof -ti :8000 | xargs kill -9
  ./start_testforge.sh
  ```

### Issue 2: Local Ollama Model Reports Offline
- **Symptom:** Telemetry displays `Active Provider: None (Offline)` or `Deterministic AST Synthesizer`.
- **Cause:** Ollama service is not running on port 11434.
- **Resolution:** Run `ollama serve &` in a separate terminal. Verify connectivity via `curl http://127.0.0.1:11434/api/tags`.

### Issue 3: SQLite Database Locked / WAL Accumulation
- **Symptom:** `sqlite3.OperationalError: database is locked`.
- **Cause:** Multiple concurrent processes reading/writing `qa_artifacts/testforge_checkpoints.db` without releasing transactions.
- **Resolution:** TestForge uses WAL mode. Run `PRAGMA wal_checkpoint(TRUNCATE);` via python:
  ```bash
  .venv-release/bin/python -c "import sqlite3; con = sqlite3.connect('qa_artifacts/testforge_checkpoints.db'); con.execute('PRAGMA wal_checkpoint(TRUNCATE);'); con.close(); print('WAL Checkpointed')"
  ```

### Issue 4: Pytest Network Hang in Mode C Ingestion
- **Symptom:** `tests/test_mode_c_ingestion.py` pauses for ~15 seconds.
- **Cause:** Test is verifying GitHub API rate-limiting or network error fallbacks using live HTTP timeouts.
- **Resolution:** This is expected defensive behavior; tests have strict 10s timeouts and pass cleanly.

