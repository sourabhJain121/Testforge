# TestForge — Milestone 1.1 Known Limitations & Boundaries

**Milestone:** Phase 1, Milestone 1.1: Canonical Task Lifecycle State Machine (GAP-01)  
**Date:** 2026-10-25  

---

## 1. Intentionally Deferred Capabilities (Scoped to Milestones 1.2 & 1.3)

1. **Dynamic MCP Tool Call Ingestion (GAP-02):**
   - The lifecycle state machine defines `INGESTING` and `PLANNING` states and records stage durations, but dynamic runtime MCP tool calling (`read_text_file`, `get_repository_info`) by the orchestrator planning loop is explicitly scheduled for Milestone 1.2.
2. **Automatic Checkpoint Resumption (GAP-03):**
   - The state machine provides valid transition paths for `RECOVERING` and `RECOVERED` states, and supports serialization (`to_dict` / `from_dict`), but automated end-to-end task recovery from SQLite checkpoints upon process restart belongs to Milestone 1.3.

---

## 2. In-Memory Process Scope vs Distributed Workers

1. **In-Process FSM Concurrency:**
   - `TaskLifecycleFSM` relies on Python's re-entrant lock (`threading.RLock`) for thread-safe state transitions within a single backend server process.
   - For multi-process or clustered distributed worker deployments (e.g. Celery / Ray), state transitions must be serialized via SQLite WAL transaction locks or distributed locks (Redis / etcd).
2. **Subprocess Sandboxing:**
   - Sandbox workers execute tests in isolated Python subprocesses with `RLIMIT_AS`. The lifecycle transitions are coordinated by the parent orchestrator process, which monitors subprocess timeouts and cancellation signals.

---

## 3. Upstream Warning Environment

1. **CrewAI 0.102.0 Deprecation Notices:**
   - CrewAI emits upstream deprecation warnings regarding Pydantic v2 argument migrations (`function_calling_llm`, `allow_code_execution`). In accordance with core operating rules, these warnings are preserved without artificial global suppression.
2. **FastAPI Lifespan Deprecation Notices:**
   - Starlette/FastAPI emits deprecation warnings regarding `@app.on_event("startup")` in favor of lifespan context managers. This does not affect functional behavior or test outcomes.
