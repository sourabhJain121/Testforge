# 02 — Dual-Frontend Architecture & Ecosystem Analysis

**TestForge Master Frontend Playground Audit**  
**Audit Target:** Streamlit (`app.py` on `:8501`) vs FastAPI Web Dashboard (`server.py` + `frontend/` on `:8000`)  
**Date:** 2026-10-30  

---

## 1. Executive Discovery & Timeline Analysis

TestForge contains two distinct user interfaces developed at different stages of the project lifecycle:

```
[September 19, 2026: Commit 6d9366c]
Streamlit Workbench (app.py :8501)
├── Rapid prototype & academic demonstration UI
├── In-process Python invocation (no REST layer)
└── Interactive Streamlit widgets & Graphviz call graph
       │
       ▼ [Evolution to Enterprise Agent Architecture]
[October 25–27, 2026: Commits 854b4c6, fb430b5, dc040f0]
FastAPI Modern Web Dashboard (server.py + frontend/ :8000)
├── Enterprise Single Page Application (SPA)
├── 46 REST API Endpoints + OpenAPI 3.1 (/docs & /redoc)
├── Real-Time WebSocket Telemetry (/ws/events)
├── FastMCP Tools Inspection & Execution Modal
├── A2A AgentCard Discovery & Test Modal
├── SQLite Blackboard Persistence & Deterministic Diffing
└── Asynchronous Background Job Lifecycle with Safe Cancellation
```

---

## 2. In-Depth Technical Investigation (12 Key Inquiries)

### 1. Why were two frontends created?
- **Streamlit (`app.py`):** Created during the early development phase (September 2026) to provide immediate graphical controls for `TargetManagerAgent`, AST inspection, and the iterative reflection loop without needing web development overhead.
- **FastAPI Dashboard (`server.py` + `frontend/`):** Created later (October 2026) to fulfill rigorous multi-agent enterprise architecture criteria, including asynchronous job management, FastMCP protocol tooling, A2A agent cards, persistent SQLite blackboard diffing, and real-time WebSocket broadcasting.

### 2. Which frontend was created first?
- **Streamlit (`app.py`) was created first** on September 19, 2026 (Commit `6d9366c`).
- **FastAPI Web Dashboard (`server.py`) was created second** on October 25, 2026 (Commit `854b4c6`).

### 3. Which is the current primary frontend?
- **The FastAPI Web Dashboard (`http://127.0.0.1:8000/`) is the primary production cockpit.** It encapsulates 100% of the multi-agent system capabilities, including FastMCP status, A2A card discovery, background process cancellation, and SQLite checkpoint diffing.

### 4. Does Streamlit call the same backend services as FastAPI?
- **No.** Streamlit (`app.py`) imports the underlying domain classes in-process directly (`from testforge.orchestrator import TestForgeOrchestrator`, `from testforge.ingestion import TargetManagerAgent`). It does not send HTTP requests to port 8000.
- Conversely, `frontend/app.js` communicates with `server.py` strictly through REST API endpoints (`/api/harden/start`, `/api/ingest/sample`) and WebSockets (`/ws/events`).

### 5. Do both interfaces use the same orchestrator?
- **Yes.** Both instantiate `TestForgeOrchestrator` (`testforge/orchestrator.py`), passing identical parameters (`target_source_code`, `max_iterations`, `target_mutation_score`, `model_name`, `engine_mode`).

### 6. Do both use the same Blackboard/state management?
- **Partially.** Both interact with `TaskLifecycleState` and write event logs to `testforge_trace.jsonl` via `TraceLogger`.
- However, **FastAPI additionally persists snapshots to SQLite** (`SQLiteBlackboardStorage` in `testforge/persistence.py`) allowing historical checkpoint recovery and deterministic snapshot diffing. Streamlit manages interactive state via `st.session_state`.

### 7. Are there duplicated implementations of the same features?
- Ingestion logic, blast radius analysis, and hardening loop execution logic are implemented by calling the shared `testforge` Python library from both interfaces. Neither interface rewrites the core AST mutators or sandbox runners.

### 8. Are there features available in one frontend but missing from the other?
- **Exclusive to FastAPI Dashboard (`:8000`):**
  1. FastMCP Tools Status & Live Test Modal (`#btn-mcp-status` $\rightarrow$ `POST /api/mcp/test`).
  2. A2A AgentCard Discovery Modal (`#btn-a2a-card` $\rightarrow$ `POST /api/a2a/test`).
  3. Checkpoint Timeline & Deterministic Diff Inspector (`#nav-checkpoints`).
  4. Real-time background job cancellation (`#btn-cancel-hardening`).
  5. Real-time WebSocket event streaming (`/ws/events`).
  6. Academic Benchmarks & Ablation tables with Raw vs Formatted Markdown view.
  7. OpenAPI Swagger UI (`/docs`) and ReDoc (`/redoc`).
- **Exclusive to Streamlit (`:8501`):**
  1. Graphviz call graph visualizer (`st.graphviz_chart`).
  2. Tabular ADK tool deliberation table (`st.dataframe(pd.DataFrame(adk_rows))`).

### 9. Are API endpoints shared or separately implemented?
- FastAPI defines and exposes 46 REST endpoints. Streamlit does not expose API endpoints and does not consume FastAPI endpoints.

### 10. Does one frontend contain outdated functionality?
- Streamlit does not reflect the FastMCP, A2A, and SQLite checkpoint diff features added in late October. However, its core hardening and sample ingestion pipelines are fully functional and up to date with the latest `testforge` engine.

### 11. Are there conflicting ports, processes, configurations, or session states?
- Ports: `8000` (FastAPI) and `8501` (Streamlit). No port conflict.
- States: Completely isolated.
- Shared File Resource: Both write synthesized test output to `test_hardened.py`. Running live hardening simultaneously on both interfaces could cause test output collisions.

### 12. Does starting one frontend automatically start or depend on the other?
- **No.** Both processes are completely decoupled and can run independently or concurrently.

---

## 3. Required Architecture Comparison Matrix

| Feature / Capability | Streamlit (`:8501`) | FastAPI (`:8000`) | Shared Backend Implementation? |
| :--- | :--- | :--- | :--- |
| **Workspace Selection** | `st.selectbox` / `samples/` dir | `/api/samples` & `/api/ingest/sample` | Yes (`TargetManagerAgent.ingest_file`) |
| **Custom Python Upload** | `st.file_uploader` (in-memory) | `/api/ingest/upload` (multipart) | Yes (`TargetManagerAgent.ingest_file`) |
| **AST Inspection** | Syntax expander & metrics | Custom code viewer & card metrics | Yes (`ast.parse` via `TargetManagerAgent`) |
| **GitHub File Import** | URL input (`Fetch & Ingest`) | Dual Subtabs: Single File & Repo Tree | Yes (`GitHubRepoService` in `github_service.py`) |
| **Hardening Pipeline** | In-process execution with spinner | Async background worker (`/api/harden/start`) | Yes (`TestForgeOrchestrator.run`) |
| **Agent Orchestration** | `TestForgeOrchestrator` direct | `TestForgeOrchestrator` in thread | Yes (`testforge/orchestrator.py`) |
| **Blackboard State** | `st.session_state` + `TraceLogger` | SQLite Blackboard (`SQLiteBlackboardStorage`)| Shared `TaskLifecycleState`; SQLite exclusive to FastAPI |
| **FastMCP Tools** | ❌ Not Available | ✅ FastMCP Status & Live Test Modal | Handled via `testforge/mcp_server.py` |
| **A2A Agent Cards** | ❌ Not Available | ✅ A2A AgentCard Discovery & Test Modal | Handled via `server.py` (`/.well-known/agent.json`)|
| **Mutation Testing** | `ParallelSandboxRunner` direct | `ParallelSandboxRunner` in orchestrator | Yes (`testforge/sandbox.py` & `mutator.py`) |
| **Results and Reports** | Inline metrics, KPIs, diffs | Score rings, mutant filter table, diffs | Yes (`final_state` KPIs) |
| **Observability Trace** | `TraceLogger` reader & expanders | `/api/telemetry` & `/api/wiretap` | Yes (`testforge_trace.jsonl` via `TraceLogger`)|
| **Settings / Config** | Sidebar radios, sliders, API keys | Settings modal (`#btn-toggle-settings`) | Both support Gemini/OpenRouter/Local engine modes |

---

## 4. Architectural Recommendation & Decision

### Selected Recommendation: **Approach B**
> **Make the FastAPI Dashboard (`http://127.0.0.1:8000/`) the primary interface, while retaining Streamlit (`http://127.0.0.1:8501/`) as a secondary specialized data workbench.**

### Rationale:
1. **Academic & Course Completeness:** The FastAPI dashboard incorporates all required modern agentic protocols (FastMCP tool introspection, A2A agent cards, SQLite blackboard checkpoint diffing, and real-time WebSockets) which Streamlit lacks.
2. **Asynchronous Reliability:** FastAPI runs hardening jobs in background threads with cancel tokens, preventing browser request timeouts during long reflection cycles.
3. **No Code Loss:** Retaining Streamlit gives evaluators a Python-native data science workbench with Graphviz tree visualizations and rapid file experimentation.
4. **Targeted UX Improvements:**
   - In FastAPI: Ensure the header includes a direct navigation link: `"🔬 Streamlit Workbench (:8501)"`.
   - In Streamlit: Ensure the sidebar displays a prominent banner: `"⚡ Primary Dashboard: FastAPI Cockpit (:8000)"`.

