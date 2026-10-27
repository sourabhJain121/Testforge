# TestForge — Callback & Trace Provenance Verification

**Audit Date:** 2026-10-27 01:18:00 IST  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Callback Architecture (MUST 5 Verification)

TestForge implements an event-driven `CallbackRegistry` (`testforge/callbacks.py`):
- **Lifecycle Events Emitted:** `step_start`, `step_end`, `agent_message`, `tool_start`, `tool_end`, `error`.
- **In-Memory Ring Buffers:** Stores chronological events bounded by size to prevent memory leaks during long-running tasks.
- **WebSocket Event Broadcast:** `server.py` and `testforge/websocket_hub.py` stream callbacks directly to active WebSocket subscribers at `ws://127.0.0.1:8000/ws`.

---

## 2. Distributed Trace Provenance (MUST 10 Verification)

1. **Trace Correlation ID:** Each hardening run is assigned a unique UUID `job_id` (e.g. `eaa31160`) that propagates across all log records, Blackboard snapshots, and OpenTelemetry spans.
2. **OpenTelemetry Semantics:** Spans contain standard semantic attributes (`component`, `iteration`, `mutants.total`, `mutants.killed`, `error.type`).
3. **Trace Log Persistence:** Chronological JSONL execution traces are emitted to `testforge_trace.jsonl` with ISO-8601 timestamps and monotonic step counters.
4. **Secret Redaction:** `testforge/logger.py` enforces regex-based sanitization that automatically redacts API keys, auth tokens, and session cookies from all trace strings and log messages.
