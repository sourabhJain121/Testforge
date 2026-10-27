# TestForge — Complete Application Inventory

**Timestamp:** 2026-10-27 00:52:00  
**Environment:** macOS Apple Silicon (arm64), Python 3.13 (`.venv-release`), FastAPI / Uvicorn + Vanilla HTML5/CSS/ES6  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`

---

## 1. Overview & Inventory Scope

TestForge is a full-stack autonomous agentic unit test hardening system. The architecture couples:
- **Backend**: A FastAPI application (`server.py`) serving a REST API, WebSocket streams (`/ws`), A2A AgentCard endpoints (`/.well-known/agent.json`), static asset serving (`/static`), and pipeline execution orchestration.
- **Frontend**: A high-performance, single-page application (`frontend/index.html`, `frontend/app.js`, `frontend/style.css`) built with responsive glassmorphism, dynamic SVG call graph rendering, live multi-agent wiretap streams, and checkpoint diff visualization.
- **Agent Pipeline**: A dual-framework orchestrator running Google ADK test generation and CrewAI adversarial critic reflection coordinated across a typed 5-space Blackboard (`testforge/blackboard.py`).

This inventory captures every frontend navigation view, interactive control, modal, backend route, and cross-cutting workflow.

---

## 2. Frontend Views & Navigation Architecture

The frontend layout is organized into a persistent top navigation bar, quick-action status pills, a hero workflow header, and 9 primary tabbed content panels:

### Navigation Views

| Tab ID | Tab Name & Icon | Purpose & Description | Primary DOM Container | State Dependencies |
|---|---|---|---|---|
| `tab-mode-a` | 📁 Mode A: Workspace & Upload | Upload single Python files, multi-file modules, or select from built-in sample fixtures (`samples/`). | `#tab-mode-a` | `selectedFile`, `fileContent`, `fileSize` |
| `tab-mode-b` | ✨ Mode B: AI Synthesis | Direct natural language prompt to generate code and hardening test suites from scratch. | `#tab-mode-b` | `promptText`, `modelTier` |
| `tab-mode-c` | 🐙 Mode C: GitHub Direct Import | Import public GitHub repositories or pull requests directly via GitHub MCP / REST. | `#tab-mode-c` | `repoUrl`, `githubToken` |
| `tab-blast` | 🎯 Blast Radius & Call Graph | Interactive AST dependency graph showing call hierarchy, complexity, and mutation risk. | `#tab-blast` | `callGraphData`, `selectedNode` |
| `tab-hardening`| ⚡ Hardening Lab & Results | The core execution cockpit: live execution controls, progress bar, mutation kill metrics, and test editor. | `#tab-hardening` | `pipelineState`, `jobId`, `metrics`, `testSuite` |
| `tab-wiretap` | 🕵️ Multi-Agent Wiretap | Real-time conversation stream showing structured handoffs between Google ADK and CrewAI. | `#tab-wiretap` | `wiretapEvents`, `activeAgent` |
| `tab-telemetry`| 📊 Observability Trace | OpenTelemetry spans, step execution timelines, memory profiling, and token accounting. | `#tab-telemetry` | `traceSpans`, `tokenMetrics` |
| `tab-benchmark`| 📈 Benchmarks & Ablation | 3-way empirical ablation comparison table (Handwritten vs Zero-shot vs Reflection). | `#tab-benchmark` | `benchmarkResults`, `ablationData` |
| `tab-checkpoints`| ⏱️ Checkpoint Timeline & Diff | Monotonic Blackboard snapshot history with side-by-side test suite diffing. | `#tab-checkpoints` | `snapshots`, `selectedRevision` |

### Modals & Drawers

| Modal ID | Trigger Element | Purpose | Interactive Controls |
|---|---|---|---|
| `#settings-modal` | `#btn-toggle-settings` | Configure LLM providers, model tiers (Local Ollama, Gemini, Claude, OpenAI), timeouts, and mutation budgets. | Radios, sliders (`#input-max-iterations`, `#input-timeout`), `#btn-save-settings`, `#btn-cancel-settings`. |
| `#a2a-modal` | `#btn-a2a-card` | Displays official A2A AgentCard JSON schema, capabilities, and endpoint contract. | `#btn-copy-a2a-json`, `#btn-close-a2a-footer`, `#btn-close-a2a-modal`. |
| `#mcp-modal` | `#btn-mcp-status` | Displays configured MCP tool servers (Filesystem MCP, GitHub MCP), schema definitions, and health. | `#btn-copy-mcp-json`, `#btn-close-mcp-footer`, `#btn-close-mcp-modal`. |

---

## 3. Interactive Controls Inventory Summary

A total of **74 distinct interactive controls** have been cataloged in `FRONTEND_INTERACTION_INVENTORY.csv`:
- **51 Buttons**: Action triggers (Run, Cancel, Export, Copy, Clear, Zoom, Filter).
- **13 Inputs & Sliders**: File selectors, iteration limits, timeouts, prompt inputs.
- **5 Select Dropdowns**: Preset fixture selectors, framework selectors, diff views.
- **5 Textareas / Code Editors**: Source code editor, generated test preview, wiretap filter.

---

## 4. Backend API Route Inventory Summary

A total of **26 REST and WebSocket routes** are registered in `server.py` and cataloged in `API_ROUTE_INVENTORY.csv`:
- **System & Health**: `/`, `/health`, `/readyz`, `/api/status`, `/ws`.
- **Pipeline Execution**: `/api/harden` (POST), `/api/cancel` (POST), `/api/run-tests` (POST), `/api/wiretap` (GET).
- **AST & Analysis**: `/api/blast-radius` (POST), `/api/call-graph` (POST), `/api/samples` (GET).
- **A2A Protocol**: `/.well-known/agent.json` (GET), `/a2a/task` (POST), `/a2a/status/{task_id}` (GET), `/a2a/cancel/{task_id}` (POST).
- **MCP Integration**: `/api/mcp/tools` (GET), `/api/mcp/call` (POST).
- **Benchmarking & Reports**: `/api/benchmark/run` (POST), `/api/benchmark/results` (GET), `/api/benchmark/markdown` (GET).
- **Observability & Checkpoints**: `/api/telemetry/spans` (GET), `/api/blackboard/checkpoints` (GET), `/api/blackboard/checkpoint/{id}` (GET).

---

## 5. Potential Gaps & Inventory Audit Notes

1. **Static Mount vs API Prefix**: `server.py` mounts `/static` for assets and handles `/` by reading `frontend/index.html`. All relative scripts (`style.css`, `app.js`) are served smoothly.
2. **WebSocket Fallback**: `app.js` attempts a WebSocket connection to `ws://.../ws`. If disconnected, polling mechanisms automatically query `/api/status` or active task endpoints to prevent silent failure.
3. **Deterministic Fallback Visibility**: All synthetic test execution modes clearly tag metrics with `data-provenance` ("deterministic_fallback" vs "live_llm") in compliance with Teacher MUST 3 and MUST 9.
