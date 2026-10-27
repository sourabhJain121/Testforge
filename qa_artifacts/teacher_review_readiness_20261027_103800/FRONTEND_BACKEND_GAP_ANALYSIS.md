# TESTFORGE — FRONTEND–BACKEND GAP ANALYSIS & CONTRACT AUDIT

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:43:00+05:30`  
**Auditor Role:** Full-Stack & Integration Reviewer  

---

## 1. Feature-by-Feature Demonstration Capability Matrix

| Feature to Demonstrate | Existing UI Navigation | Backend Endpoint | Status in UI | Identified UX / Technical Gap |
| :--- | :--- | :--- | :---: | :--- |
| **1. Source Hardening** | `📁 Mode A` $\rightarrow$ `🔥 Hardening Lab` | `POST /api/harden/start`<br>`GET /api/harden/status/{id}` | Functional | Progress bar uses simulated timer (`progressSim += 12%`) rather than real backend FSM stage. |
| **2. Baseline Validation** | `🔥 Hardening Lab` | `job.final_state.baseline_run` | Functional | Displays tests generated/passed/failed correctly. |
| **3. Blackboard & Handoffs** | `💾 Checkpoint Timeline` | `GET /api/checkpoints`<br>`GET /api/checkpoints/diff` | Functional | Full 5-space partition view is separated in the Checkpoint tab rather than shown live in the Lab tab. |
| **4. Mutation Results** | `🔥 Hardening Lab` | `job.final_state.mutants` | Functional | Interactive table with filters (`KILLED`, `SURVIVED`, `EQUIVALENT`). Diff pane shows AST diff and sandbox latency. |
| **5. MCP Integrations** | Header `🔌 MCP Tools` | `GET /api/mcp/status` | Functional | Lists FastMCP servers and 4 tools. Lacks a 1-click test button to execute a tool inside the modal. |
| **6. A2A Protocol** | Header `🤖 A2A Agent Card` | `/.well-known/agent-card.json`<br>`POST /a2a/tasks` | Functional | Displays official AgentCard schema. Lacks an in-browser "Test A2A Ping" button. |
| **7. Frameworks (CrewAI/ADK)**| `🤖 Multi-Agent Wiretap` | `GET /api/wiretap` | Functional | Displays explicit handoff cards with icons and message envelopes. |
| **8. Observability Trace** | `📊 Observability Trace` | `GET /api/telemetry` | Functional | Renders searchable event table with correlation IDs and token usage. |
| **9. Benchmarks & Ablation**| `⚡ Benchmarks & Ablation`| `GET /api/benchmark/results`<br>`GET /api/benchmark/markdown` | Functional | Displays 3-condition comparative table and Markdown preview. |
| **10. Security Behavior** | `📁 Mode A`, `🌐 Mode C` | Pre-execution AST scanner | Functional | Rejects dangerous calls (`os.system`, SSRF) with error alerts. Redacts secrets in logs. |
| **11. Deployment Readiness**| Navbar status pills | `GET /healthz`<br>`GET /readyz` | Functional | Shows server online status. |

---

## 2. In-Depth Contract & UI Checks

### A. Broken or Inert Buttons Check
- Checked all 38 button IDs in `frontend/index.html` against event listeners in `frontend/app.js`.
- **Verdict: ZERO INERT BUTTONS.** Every button has a bound listener, loading state, and error handling.

### B. Backend/Frontend Field Mismatches Check
- Audited JSON keys returned by `server.py` vs parsed by `app.js`.
- **Verdict: ZERO MISMATCHES.** Bidirectional aliases in `server.py:870-940` (`history` $\leftrightarrow$ `iteration_history`, `final_mutation_score` $\leftrightarrow$ `mutation_score`) ensure smooth hydration of KPI cards and tables.

### C. Loading, Error, Cancellation, and Timeout States Check
- **Loading:** Spinner states exist on all async actions (file upload, synthesis, benchmark, checkpoint inspection).
- **Error:** User-facing alerts render backend error strings gracefully without breaking the layout.
- **Cancellation:** `POST /api/harden/cancel/{id}` cleanly halts subprocesses; UI renders `verdict-banner cancelled`.
- **Timeout:** Subprocess timeout guardrail (5.0s) catches infinite loops; UI renders `verdict-banner timed-out`.

### D. Hardcoded vs Live Data Check
- **Checkpoint Tab:** 100% dynamic; queries SQLite `testforge_checkpoints.db`.
- **Telemetry Tab:** 100% dynamic; reads `testforge_trace.jsonl`.
- **Wiretap Tab:** 100% dynamic; reads inter-agent handoff traces.
- **Benchmark Tab:** 100% dynamic; loads `benchmark_results.json`.
- **Hardening Tab Results:** 100% dynamic; loads `job.final_state`.
- **Hardening Tab Progress:** **PARTIALLY SIMULATED.** While running, `progressSim = Math.min(progressSim + 12, 90)` generates a simulated percentage rather than displaying real FSM states.

---

## 3. Targeted UI Recommendations

Instead of an unnecessary full redesign, four minimal adjustments will optimize the UI for the teacher review:

1. **Wire Hardening Progress Bar to Real FSM State:** Replace `progressSim` with `job.lifecycle_state` and display descriptive phase labels.
2. **Add a Live Blackboard Partition Strip in Hardening Lab:** Render a 5-pill status strip under the progress bar that lights up as agents write to `Target`, `Suite`, `Mutants`, `Critic`, and `Metrics`.
3. **Add 1-Click Test Ping in A2A Modal:** Allows instant in-browser demonstration of A2A JSON-RPC execution.
4. **Add 1-Click FastMCP Tool Query in MCP Modal:** Allows instant in-browser demonstration of FastMCP stdio tool calls.
