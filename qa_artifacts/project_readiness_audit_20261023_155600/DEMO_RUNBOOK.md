# TestForge — Evaluator Demonstration Runbook

**Target Audience:** Evaluators, Professors, Viva Examiners, and Demonstrators  
**Platform:** macOS / Linux  
**Environment:** `.venv-release` (Python 3.13.17)  
**Primary URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  
**Primary Daemon Entry Point:** `server.py` (FastAPI + Uvicorn)

---

## 1. Quick Verification & Prerequisites

Before beginning the evaluation session, verify in macOS Terminal:

```bash
cd /Users/sourabh/TestForge

# 1. Verify virtual environment Python version
.venv-release/bin/python --version
# Expected: Python 3.13.17

# 2. Verify all dependencies are clean
.venv-release/bin/pip check
# Expected: No broken requirements found.

# 3. Verify Docker configuration validity (optional containerized check)
docker compose config
# Expected: valid compose yaml printed without errors
```

---

## 2. Server Startup & Verification

### A. Starting the TestForge Backend

If the server is not already running, launch it in a dedicated Terminal window or background process:

```bash
cd /Users/sourabh/TestForge
.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

> **Note on Currently Running Process:** If port 8000 is already bound, check its PID:
> ```bash
> lsof -i :8000
> ```

### B. Health and Readiness Endpoints

Verify the server is healthy and ready to serve requests:

```bash
# 1. Health check probe
curl -i http://127.0.0.1:8000/healthz
# Expected: HTTP/1.1 200 OK
# Response: {"status":"healthy","service":"testforge-backend","version":"2.0.0"}

# 2. Readiness check probe
curl -i http://127.0.0.1:8000/api/ready
# Expected: HTTP/1.1 200 OK
# Response: {"ready":true,"blackboard_connected":true,"db_connected":true}

# 3. WebSocket Hub status
curl -i http://127.0.0.1:8000/api/ws/status
# Expected: HTTP/1.1 200 OK
# Response: {"active_connections":...,"total_connections_served":...,"message_queue_size":0}

# 4. A2A Discovery Agent Card probe
curl -i http://127.0.0.1:8000/.well-known/agent-card.json
# Expected: HTTP/1.1 200 OK, application/json with valid A2A AgentCard schema
```

---

## 3. Opening the Dashboard in Google Chrome

Open Google Chrome to the primary TestForge dashboard:

```bash
open -a "Google Chrome" http://127.0.0.1:8000/
```

### Visual Landmarks to Confirm
1. **Header:** Title **TestForge** with subtitle *"Multi-Agent Mutation Testing & Self-Healing Engine"*.
2. **Status Pills:** Backend Status (`Online`), WebSocket indicator (`Live (WS)` or `Polling` fallback), Mode selector pills (`Mode A (Single File)`, `Mode B (Repository)`, `Mode C (Git PR)`).
3. **Action Buttons:** `A2A Card` in top right header, `Run Fast Benchmark` pill, `Checkpoints` trigger.
4. **Primary Panels:**
   - Left Column: Target Code selection / AST Viewer / Test Generation Controls.
   - Right Column: Mutation Score KPI gauge, Survival Breakdown, Wiretap Event Stream.

---

## 4. Five-Minute Structured Viva Demonstration

Follow this exact sequence to demonstrate the core capabilities to an evaluator:

### Step 1: Target Ingestion & AST Inspection (Mode A)
1. In the target selector dropdown, choose **`samples/rate_limiter.py`**.
2. Click **"Inspect AST"**.
3. **What to show the evaluator:**
   - The AST nodes parsed by `testforge/ast_engine.py` (Functions, Classes, Branches).
   - Point out that mutations are syntax-aware AST transformations rather than naive regex text replacements.

### Step 2: Adversarial Mutation Generation
1. Click **"Generate Mutants"** (or use the Hardening Lab controls).
2. **What to show the evaluator:**
   - 8 AST mutation operator families: `AOR` (Arithmetic), `ROR` (Relational), `COR` (Conditional), `LCR` (Logical), `UOI` (Unary), `SBR` (Statement Block Removal), `BCR` (Boolean Constant), `EXC` (Exception).
   - Highlight the static equivalence filter (`testforge/ast_engine.py:is_equivalent_mutant`) which prunes syntactic tautologies (e.g., `x = x + 0`, `a and True`).

### Step 3: Hardening Loop & Live WebSocket Streaming
1. Click **"Start Hardening"**.
2. **What to show the evaluator:**
   - Observe the **Live Wiretap** feed updating in real time.
   - Point out the WebSocket badge (`Live (WS)`).
   - Emphasize that the backend broadcasts via `testforge/websocket_hub.py` using bounded ring-buffers (1,000 events) and client-level 100-event drop-oldest queues to prevent memory leaks.
   - If an agent generates tests, show how subprocess test execution is isolated in `testforge/executor.py` with resource caps (memory/timeout guardrails).

### Step 4: Mutation Score & Denominator Adjustment
1. Review the final KPI gauges:
   - **Baseline Mutation Score** vs **Hardened Mutation Score**.
   - Show how the score formula:
     $$\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Mutants} - \text{Equivalent Mutants}} \times 100$$
     adjusts for surviving vs equivalent mutants.
2. Click on a mutant row to view the inline side-by-side AST Diff modal.

### Step 5: Checkpoints, Timeline & Non-Destructive Restore
1. Click the **"Checkpoints"** button in the header.
2. **What to show the evaluator:**
   - SQLite-backed state history from `testforge/persistence.py`.
   - Click **"View Diff"** on any checkpoint to inspect the unified diff of code and test changes.
   - Click **"Restore"**; observe the safety confirmation modal dialog.
   - Click **"Cancel"** to demonstrate safe abort without state corruption.

### Step 6: A2A (Agent-to-Agent) Interoperability
1. Click the **"A2A Card"** button in the top-right header.
2. **What to show the evaluator:**
   - A human-readable modal displays agent capabilities, protocols (`A2A v0.3`), supported tools (`FastMCP`), input/output schemas, and endpoint references.
   - Click **"Copy JSON"** to demonstrate clipboard integration (shows momentary "Copied!" feedback).
   - Click **"Raw JSON"** to demonstrate that `/.well-known/agent-card.json` serves machine-to-machine agents compliant with the A2A discovery standard.
   - Press **Escape** or click the close icon `×` to dismiss the modal cleanly.

### Step 7: Fast Benchmark Demonstration
Run the deterministic fast benchmark directly from macOS Terminal:

```bash
.venv-release/bin/python run_benchmark.py --fast -r 5
```

**Evaluator Disclosure Points:**
- Clearly state that `--fast` runs offline deterministic mock fixtures (`benchmark_fast_mode.py`) designed for sub-second CI validation without incurring cloud LLM latency or API costs.
- Show the formatted console table displaying runs, survival rates, and latency metrics.

---

## 5. Running Automated Verification Commands

### A. Run Full Test Suite (309 Tests)
```bash
.venv-release/bin/python -m pytest tests/ -q
```
*Expected Result:* `309 passed, 208 warnings in ~200-220s` (warnings are standard CrewAI upstream deprecations).

### B. Run Fast Subsystem Tests (Sub-second to 5s)
For rapid during-viva verification without running all 309 tests:

```bash
# 1. WebSocket & Fast Benchmark tests (11 passed in ~0.3s)
.venv-release/bin/python -m pytest tests/test_websocket_events.py tests/test_fast_benchmark.py -q

# 2. A2A Protocol & Agent Card tests (36 passed in ~0.5s)
.venv-release/bin/python -m pytest tests/test_a2a_protocol.py tests/test_a2a_card_ui_and_endpoint.py -q

# 3. AST Mutation & Equivalence tests (18 passed in ~0.4s)
.venv-release/bin/python -m pytest tests/test_ast_engine.py tests/test_equivalence.py -q

# 4. Checkpoint persistence & diff tests (22 passed in ~0.6s)
.venv-release/bin/python -m pytest tests/test_persistence.py tests/test_checkpoint_diff_ui.py -q
```

---

## 6. Safe Server Shutdown

To safely stop the TestForge server after the demonstration:

```bash
# 1. Identify the process ID listening on port 8000
lsof -i :8000

# 2. Terminate gracefully using SIGTERM
kill $(lsof -t -i:8000)

# 3. Verify port 8000 is released
lsof -i :8000
# (Should return no output)
```
