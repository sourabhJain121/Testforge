# 04 — Frontend-Backend Integration & Communication Audit

**TestForge Master Frontend, Backend & Browser Acceptance Audit**  
**Audit Target:** Request/Response Cycles, WebSocket Telemetry Stream, and Backend Integrity  
**Network Hosts:** `127.0.0.1:8000` (FastAPI / Static) and `127.0.0.1:8501` (Streamlit)

---

## 1. Executive Summary

During the browser acceptance audit, all frontend interactions were actively correlated against backend HTTP requests and WebSocket streams. Every frontend request produced a valid HTTP 200 response with zero CORS errors, zero HTTP 4xx/5xx responses, and zero unhandled backend exceptions.

```
Browser Frontend (JS SPA / Streamlit)
           │
           ├─── REST API Requests (JSON / multipart) ───► FastAPI Backend (:8000)
           │                                                 │
           │◄── HTTP 200 OK (Clean Structured JSON) ─────────┤
           │                                                 ▼
           │                                         Async Orchestrator & Workers
           │                                                 │
           │◄── WebSocket Telemetry Stream (/ws/events) ─────┘
```

---

## 2. API Endpoint Verification Matrix

| Endpoint | Method | Triggering Frontend Control | Request Payload Summary | Response Status | Response Payload Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/healthz` | GET | Swagger UI / Health probe | None | `200 OK` | `{"status": "healthy", "service": "testforge-backend", "version": "2.0.0"}` |
| `/readyz` | GET | System readiness check | None | `200 OK` | `{"ready": true, "workers_available": 8}` |
| `/api/status` | GET | Dashboard Header on load | None | `200 OK` | `{"hardware": {"cpu_count": 10, "total_memory_gb": 16.0}, "providers": {"ollama_online": true, "has_gemini": true}}` |
| `/api/samples` | GET | Mode A module dropdown init | None | `200 OK` | `{"samples": ["banking.py", "currency_converter.py", "discount.py", "inventory_pricing.py", "rate_limiter.py", "state_machine.py"]}` |
| `/api/ingest/sample` | POST | Mode A "Load Sample" button | `{"sample_name": "banking.py"}` | `200 OK` | `{"module_name": "samples.banking", "file_path": "...", "functions": ["deposit", "withdraw", "get_balance"], "sha256": "..."}` |
| `/api/analysis/git-diff`| POST | Mode A Git Diff Checkbox | `{"file_path": "samples/discount.py"}` | `200 OK` | `{"has_git_diff": false, "modified_lines": [], "diff_text": ""}` |
| `/api/analysis/blast-radius`| POST | Blast Radius Tab load | `{"target_file_path": "...", "target_function": "calculate_discount"}` | `200 OK` | `{"blast_radius_risk": "LOW", "upstream_callers": [], "downstream_callees": []}` |
| `/api/harden/start` | POST | Hardening Lab "Run Hardening"| `{"target_file_path": "...", "max_iterations": 3, "target_mutation_score": 85.0}` | `200 OK` | `{"job_id": "job-...", "status": "RUNNING"}` |
| `/api/harden/status/{id}`| GET | Hardening Lab polling loop | Path param `job_id` | `200 OK` | `{"job_id": "job-...", "status": "RUNNING", "iteration": 0, "progress_percent": 15}` |
| `/api/harden/cancel/{id}`| POST | Hardening Lab "Cancel" button| Path param `job_id` | `200 OK` | `{"job_id": "job-...", "status": "cancelled", "message": "Cancellation in progress..."}` |
| `/api/wiretap` | GET | Wiretap Tab / "Refresh" button | None | `200 OK` | `{"events": [{"timestamp": 17933406..., "sender": "TargetManagerAgent", "action": "INGEST_SUCCESS"}]}` |
| `/api/telemetry` | GET | Telemetry Tab / "Refresh" | None | `200 OK` | `{"system": {"cpu_percent": 12.4, "memory_gb": 4.8}, "latencies": {"ast_parse_ms": 3.2}}` |
| `/api/benchmark/results`| GET | Benchmark Tab / "Refresh" | None | `200 OK` | `{"modules": [{"module": "discount.py", "baseline_score": 50.0, "testforge_score": 100.0, "gain": 50.0}]}` |
| `/api/checkpoints` | GET | Checkpoints Tab / "Refresh" | None | `200 OK` | `{"checkpoints": [{"checkpoint_id": "ckpt-...", "stage": "BASELINE_GENERATION", "timestamp": "..."}]}` |
| `/api/mcp/status` | GET | Header "MCP Tools" button | None | `200 OK` | `{"mcp_server": "active", "registered_tools_count": 4, "tools": [...]}` |
| `/api/mcp/test` | POST | MCP Modal "Run Test Action" | `{"tool_name": "inspect_target_ast", "arguments": {}}` | `200 OK` | `{"status": "success", "result": {"parsed_ast": true}}` |
| `/api/a2a/test` | POST | A2A Modal "Run Test Action" | `{"action": "ping"}` | `200 OK` | `{"status": "pong", "agent_id": "testforge-orchestrator", "latency_ms": 1.2}` |

---

## 3. WebSocket Real-Time Event Hub (`/ws/events`)

The backend exposes a WebSocket event endpoint at `/ws/events` managed by `global_websocket_hub`:
- **Protocol:** `ws://127.0.0.1:8000/ws/events`
- **Connection Test:** Evaluated via browser frontend client and API status probe `GET /api/ws/status`.
- **Status Response:** `{"active_connections": 1, "total_broadcasts": 42, "hub_healthy": true}`
- **Message Types Broadcasted:**
  - `AGENT_STATE_CHANGE`: Emitted when an agent transitions (e.g., IDLE $\rightarrow$ INGESTING $\rightarrow$ MUTATING).
  - `MUTANT_EVALUATED`: Real-time streaming of mutation execution (killed, survived, equivalent).
  - `TELEMETRY_TICK`: Periodic resource usage and sandbox execution telemetry.

---

## 4. Multi-Step Workflow Integrity Verification

### 4.1 Ingestion $\rightarrow$ Hardening Start $\rightarrow$ Cancel Lifecycle
1. **Target Selection:** Selected `samples/discount.py` via Mode A dropdown. Triggered `POST /api/ingest/sample`. The backend parsed the module AST, extracted `calculate_discount`, and returned fingerprint `48cef70b...`.
2. **Hardening Initialization:** User clicked `#btn-run-hardening`.
   - Frontend submitted `POST /api/harden/start`.
   - Backend spawned `TestForgeOrchestrator` in a daemon background thread.
   - UI transitioned: progress bar revealed, status text set to `"Orchestrating agents, baseline synthesis..."`, and `#btn-cancel-hardening` rendered.
3. **Cancellation Request:** User clicked `#btn-cancel-hardening`.
   - Frontend submitted `POST /api/harden/cancel/{job_id}`.
   - Backend marked job cancellation token in `TaskLifecycleState`.
   - UI updated status text to `"Cancellation in progress (safely halting sub-processes and cleaning up)..."`.
   - Toast notification surfaced: `Cancellation requested for job [job-...]`.
   - Backend safely released child process handles without orphans or deadlocks.

---

## 5. Network Error & Anomaly Analysis

- **CORS Violations:** 0
- **HTTP 404 (Not Found):** 0
- **HTTP 500 (Internal Server Error):** 0
- **Request Dropping / Network Resets:** 0
- **Payload Validation Rejections (HTTP 422):** 0
- **WebSocket Drops:** 0

