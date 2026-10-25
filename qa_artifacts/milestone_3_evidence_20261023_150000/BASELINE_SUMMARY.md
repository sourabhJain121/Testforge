# TestForge — Milestone 3 Baseline Summary

**Audit Date:** October 23, 2026
**Workspace:** `/Users/sourabh/TestForge`
**Environment:** Python 3.13.17 (`.venv-release`), Node.js v24.15.0, Uvicorn on `http://127.0.0.1:8000`

---

## 1. Baseline Test Verification
- **Command:** `.venv-release/bin/python -m pytest tests/ -q`
- **Result:** `298 passed, 206 warnings in 357.33s (0:05:57)`
- **Exit Code:** `0`
- **Focused A2A Test Suite:**
  - `tests/test_a2a_protocol.py`
  - `tests/test_a2a.py`
  - `tests/test_a2a_card_ui_and_endpoint.py`
  - Result: `36 passed in 4.91s`

## 2. Static Integrity Checks
- `node -c frontend/app.js`: Exit Code `0`
- `.venv-release/bin/python -m compileall testforge/ tests/ -q`: Exit Code `0`
- `.venv-release/bin/pip check`: Exit Code `0` ("No broken requirements found.")
- `git diff --check`: Exit Code `0` (clean, 0 whitespace errors)

## 3. Git Status Before Milestone 3
- Tracked modified files: 21 files (`.gitignore`, `README.md`, `app.py`, `benchmark_results.json`, `requirements.txt`, `run_benchmark.py`, `samples/github_requests_status_codes.py`, `test_hardened.py`, `testforge/agents.py`, `testforge/classifier.py`, `testforge/ingestion.py`, `testforge/llm_client.py`, `testforge/logger.py`, `testforge/mutator.py`, `testforge/orchestrator.py`, `testforge/sandbox.py`, `testforge/state.py`, `testforge_trace.jsonl`, `tests/test_blast_and_adk.py`, `trace_reflected.jsonl`, `trace_zeroshot.jsonl`).
- Untracked files preserved: All QA artifacts, documentation, SQLite checkpoints, test suites, and frontend components.

## 4. Current Observability & Benchmarking State
- **Observability:** `TraceLogger` appends to `testforge_trace.jsonl`. Frontend polls `/api/wiretap` and `/api/telemetry` over HTTP GET every 3–5 seconds. No WebSocket streaming endpoint currently exists.
- **Benchmarking:** `run_benchmark.py` and `testforge/benchmarking.py` execute full AST sandbox subprocesses with LLMs/sandbox, taking ~4–6 minutes for multi-run repetitions. No `--fast` deterministic offline benchmark mode currently exists.
