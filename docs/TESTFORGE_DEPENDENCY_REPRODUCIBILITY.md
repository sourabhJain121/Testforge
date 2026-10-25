# TestForge — Dependency Reproducibility & Environment Guide

**Document:** `docs/TESTFORGE_DEPENDENCY_REPRODUCIBILITY.md`  
**Date:** October 22, 2026  
**Auditor / Platform Engineer:** Senior Platform Engineer & Release Architect  
**Workspace:** `/Users/sourabh/TestForge`  
**Clean Release Environment:** `.venv-release` (Python 3.13.17)  
**Docker Image Verified:** `testforge:release-test` (`python:3.13-slim`)  
**Evidence Artifacts:** `qa_artifacts/dependency_reproducibility_20261022/`  

---

## 1. Supported Python Runtime Policy

- **Primary Supported Runtime:** **Python 3.13** (specifically tested on Python 3.13.17 `arm64` and Linux container `aarch64`).
- **Python 3.14 Status:** **INCOMPATIBLE / UNSUPPORTED**. Python 3.14 lacks pre-compiled wheels for essential C-extension dependencies required by `crewai` (specifically `aiohttp`, `yarl`, `frozenlist`, and `multidict`), and source compilation fails against Python 3.14 C-API header changes.
- **Python 3.11 / 3.12 Status:** Supported for standard library and core FastAPI; Python 3.13 provides modern AST parsing and is the validated production target.
- **Hardware Acceleration:** Native Apple Silicon GPU/Metal acceleration via MLX (`mlx`, `mlx-metal`) is supported dynamically via optional import hooks in `testforge/accel.py`. On Linux container environments, it gracefully falls back without requiring Metal drivers.

---

## 2. Dependency Architecture & Rationale

The root `requirements.txt` was expanded from an incomplete 6-package stub into a complete, defensible manifest declaring all direct dependencies required for runtime execution, agent orchestration, background mutation sandboxing, and web serving.

### A. Manifest Taxonomy

```text
# --- Core Web API & Application Server ---
fastapi>=0.140.0,<1.0.0      # Primary backend REST API & WebSocket server
uvicorn>=0.30.0,<1.0.0       # High-performance ASGI server for FastAPI
streamlit>=1.35.0,<2.0.0     # Alternative interactive analytical dashboard
python-dotenv>=1.0.0,<2.0.0  # Automatic .env credential loading

# --- State, Schema & Validation ---
pydantic>=2.7.0,<3.0.0       # Strict runtime validation & typed state models
pydantic-settings>=2.2.0,<3.0.0 # BaseSettings configuration management

# --- Agentic Frameworks & Protocol Integrations ---
crewai>=1.15.0,<2.0.0        # CrewAI multi-agent sequential critic pipeline
google-adk>=1.14.0,<2.0.0    # Google Agent Development Kit for test synthesis
google-genai>=0.1.1,<2.0.0   # Official Gemini Generative AI SDK
mcp>=1.28.0,<2.0.0           # Model Context Protocol FastMCP server & client
a2a-sdk>=0.3.0,<1.0.0        # Agent-to-Agent task delegation & card discovery

# --- Networking, Ingestion & Serialization ---
httpx>=0.27.0,<1.0.0         # Async HTTP client for OpenRouter & GitHub Mode C
requests>=2.31.0,<3.0.0      # Synchronous HTTP utilities & probes
PyYAML>=6.0.0,<7.0.0         # Agent configuration and persona serialization
pandas>=2.2.0,<4.0.0         # Tabular dataframes in benchmark reports

# --- Diagnostics, Hardware Monitoring & Logging ---
psutil>=5.9.0,<8.0.0         # Process monitoring & CPU/RAM sandbox guardrails
rich>=13.7.0,<15.0.0         # Console syntax highlighting & trace formatting

# --- Test Execution & Mutation Sandbox Engine ---
pytest>=8.0.0,<10.0.0        # Primary test runner and sandbox execution engine
pytest-cov>=5.0.0,<8.0.0     # Coverage plugin for sandbox pytest runs
coverage>=7.0.0,<8.0.0       # AST mutation line coverage measurement engine
```

### B. Resolved Environment Lock
A frozen, reproducible lock of all 187 direct and transitive packages installed during the clean verification run has been preserved at:
`qa_artifacts/dependency_reproducibility_20261022/requirements_resolved.lock`

---

## 3. Clean-Install Verification Results

A clean virtual environment was instantiated at `/Users/sourabh/TestForge/.venv-release` using system Python 3.13 (`/opt/homebrew/bin/python3.13 -m venv .venv-release`).

1. **Dependency Installation (`pip install -r requirements.txt`):**
   - Exit Code: **0** (Clean)
   - Log: `qa_artifacts/dependency_reproducibility_20261022/pip_install.log`
2. **Dependency Consistency (`pip check`):**
   - Output: `No broken requirements found.`
   - Exit Code: **0**
   - Log: `qa_artifacts/dependency_reproducibility_20261022/pip_check.log`
3. **Direct Framework Imports:**
   - Script: `.venv-release/bin/python -c "import fastapi, uvicorn, streamlit, pydantic, crewai, google.adk, mcp, a2a, pytest, coverage, requests, httpx, psutil, rich, dotenv, pandas, yaml; import server"`
   - Output: `ALL DIRECT IMPORTS SUCCESSFUL! server.py imported successfully!`
   - Exit Code: **0**
4. **Targeted Regression Suite (105 tests):**
   - Command: `.venv-release/bin/python -m pytest test_hardened.py tests/test_deployment.py tests/test_crew_critic.py tests/test_blackboard.py tests/test_mcp.py tests/test_security.py -v`
   - Passed: **105 / 105 passed** in 18.18s
   - Exit Code: **0**
5. **Full Project Test Suite (206 tests):**
   - Command: `.venv-release/bin/python -m pytest tests/ -q`
   - Passed: **206 / 206 passed** in 207.80s (0:03:27)
   - Exit Code: **0**

---

## 4. Docker Container Build & Local Deployment Results

### A. Docker Configuration Validation
- Command: `docker compose config`
- Result: **Valid Compose Schema (Exit Code 0)**. Successfully mapped `backend` (FastAPI:8000) and `dashboard` (Streamlit:8501).

### B. Container Image Build
- Command: `docker build -t testforge:release-test .`
- Context: Local workspace excluding ignored `.venv*`, caches, and Git history.
- Base Image: `python:3.13-slim` (Debian Linux `aarch64`)
- Duration: 214.3 seconds
- Output: `naming to docker.io/library/testforge:release-test done`
- Exit Code: **0**
- Log: `qa_artifacts/dependency_reproducibility_20261022/docker_build.log`

### C. Live Container Runtime Verification
The built image was launched on an alternative port (8001) to verify runtime health without conflicting with the developer's local active Uvicorn process (PID 29110):

```bash
docker run --rm -d --name testforge-verify-run -p 8001:8000 testforge:release-test
curl -s http://127.0.0.1:8001/healthz
curl -s http://127.0.0.1:8001/readyz
docker stop testforge-verify-run
```

**Observed Responses:**
- `/healthz`: `{"status":"healthy","service":"testforge-backend","version":"2.0.0"}` (HTTP 200)
- `/readyz`: `{"status":"ready","service":"testforge-backend","subsystems":{"ast_mutator":"operational","blackboard":"operational","sandbox_storage":"operational"}}` (HTTP 200)
- Container cleanly terminated with exit code 0.
- Log: `qa_artifacts/dependency_reproducibility_20261022/docker_container_verification.json`

---

## 5. Local Setup Instructions for New Developers

To onboard onto a clean machine:

```bash
# 1. Clone repository
git clone <repo-url>
cd TestForge

# 2. Create Python 3.13 virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip & install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify installation
python -m pip check
pytest test_hardened.py -v

# 5. Launch FastAPI backend
uvicorn server:app --host 127.0.0.1 --port 8000

# 6. (Optional) Run via Docker Compose
docker compose up --build
```

---

## 6. Known Limitations

1. **Host Python 3.14:** Running `pip install -r requirements.txt` under Python 3.14 will fail on macOS arm64 due to upstream `aiohttp` wheel absence. Developers must use Python 3.13.
2. **Third-Party Upstream Warnings:** CrewAI and Google Cloud AIPlatform emit 188 deprecation warnings for upcoming major releases (`function_calling_llm` and storage version bumps). These do not impact execution or correctness.
3. **Container GPU MLX:** Apple Silicon Metal MLX acceleration is unavailable in Linux Docker containers; the container automatically runs CPU worker process pools.
