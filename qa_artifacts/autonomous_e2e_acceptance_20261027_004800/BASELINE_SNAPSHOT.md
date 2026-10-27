# TestForge — Baseline Snapshot & Preservation State
## Autonomous E2E Audit & Acceptance Pass

**Audit Timestamp:** 2026-10-27T00:48:00+05:30  
**Repository:** `/Users/sourabh/TestForge`  
**Execution Environment:** macOS Apple Silicon arm64 | Python 3.13.18 (`.venv-release`)  
**Audit Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Initial Repository State

- **Branch:** `main` (clean tracking of `origin/main`).
- **Recent Commit:** `854b4c6 feat: complete final major milestones, teacher requirements, full browser acceptance audit, and demo rehearsal`.
- **Pre-Existing Staged Changes:**
  - Modified `.gitignore` (incorporating test and cache filters).
  - Deleted historical root trace files (`testforge_trace.jsonl`, `trace_reflected.jsonl`, `trace_zeroshot.jsonl`).
  - *Preservation status:* **Intact in index, completely untouched.**
- **Pre-Existing Working Tree Modifications:**
  - `testforge/agents.py`, `testforge/blackboard.py`, `testforge/corpus/runner.py`, `testforge/llm_client.py`, `testforge/mutator.py`, `testforge/orchestrator.py`, `testforge/sandbox.py`, `testforge/state.py`.
  - Historical benchmark files: `benchmark_results.json`, `benchmark_results.md`, `test_hardened.py`.
  - Untracked files: `testforge/guidance.py`, `tests/test_mutation_guided_repair.py`, and historical `qa_artifacts/` directories.
  - *Preservation status:* **All files preserved strictly as found.**

---

## 2. Process & Port Discovery

- **Port 8000 Discovery:** Discovered an older orphaned background daemon process from Oct 25 (PID 87094) that had deadlocked due to watchfiles reload exception (`ModuleNotFoundError: No module named 'pkgutil'`).
- **Remediation:** Cooperative cancellation via `manage_task` successfully halted the stale background task. Port 8000 is verified completely free.
- **Backend Launch Protocol:** `server.py` launched cleanly via `.venv-release/bin/python server.py`.
- **Frontend Serving Protocol:** `server.py` mounts `/static` from `./frontend/` and serves `/static/index.html` at the root `/`. No separate Node server is required.
