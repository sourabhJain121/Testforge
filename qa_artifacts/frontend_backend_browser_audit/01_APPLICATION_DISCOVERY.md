# 01 — Application Discovery & Entrypoint Inventory

**TestForge Master Frontend, Backend & Browser Acceptance Audit**  
**Audit Execution Date:** 2026-10-30  
**Environment:** Darwin arm64 (10 Cores, 16 GB Unified Memory)  
**Python Environment:** `/Users/sourabh/TestForge/.venv-release/bin/python` (Python 3.13.18)  
**Browser Engine:** Google Chrome 141 (via `agent-browser@0.37.1` daemon)

---

## 1. Executive Discovery Summary

TestForge exposes two primary, distinct frontend graphical interfaces and two interactive API documentation endpoints:

| Interface | Technology | Network Address | Default Port | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI Modern Web Dashboard** | HTML5 / CSS3 / Vanilla JS SPA | `http://127.0.0.1:8000/` | `8000` | Full autonomous pipeline cockpit, AST visualizer, blast radius call graph, multi-agent wiretap, observability trace, benchmarks, checkpoints, MCP/A2A modals |
| **Streamlit Hardening Workbench** | Streamlit 1.66.1 | `http://127.0.0.1:8501/` | `8501` | Rapid interactive exploration, file upload, AI module synthesis, local/cloud model switching, live mutation hardening loop |
| **FastAPI Swagger UI** | Swagger UI (OpenAPI 3.1) | `http://127.0.0.1:8000/docs` | `8000` | Interactive REST API exploration, payload validation, live endpoint execution (46 endpoints) |
| **FastAPI ReDoc** | ReDoc | `http://127.0.0.1:8000/redoc` | `8000` | Comprehensive OpenAPI specification, data model reference, schemas |

---

## 2. Startup Instructions & Process Verification

### 2.1 Backend Process (FastAPI & Dashboard)
- **Command:**  
  ```bash
  .venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
  ```
- **Process Verification:**
  - Health Endpoint: `GET http://127.0.0.1:8000/healthz` $\rightarrow$ `HTTP 200 OK`
  - Readiness Probe: `GET http://127.0.0.1:8000/readyz` $\rightarrow$ `HTTP 200 OK`
  - System Status: `GET http://127.0.0.1:8000/api/status` $\rightarrow$ `HTTP 200 OK`
  - Output: `{"status": "healthy", "service": "testforge-backend", "version": "2.0.0"}`

### 2.2 Frontend Process (Streamlit Hardening Workbench)
- **Command:**  
  ```bash
  .venv-release/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
  ```
- **Process Verification:**
  - Health Endpoint: `GET http://127.0.0.1:8501/_stcore/health` $\rightarrow$ `HTTP 200 OK ("ok")`

---

## 3. Detailed Route & Navigation Structure

### 3.1 FastAPI Web Dashboard (`http://127.0.0.1:8000/`)
The Web Dashboard is an enterprise Single Page Application organized around a top system header, modal dialogs, and a 9-tab workspace:

1. **Top Header & Utilities:**
   - Application Brand & Status Indicator (`⚡ TestForge`, `Darwin arm64`, `Ollama Online`, `Gemini Active`)
   - `🤖 A2A Card` Modal Trigger (`#btn-a2a-card`)
   - `🔌 MCP Tools` Modal Trigger (`#btn-mcp-status`)
   - `⚙️ Settings` Drawer Trigger (`#btn-toggle-settings`)
   - `🐙 Repo` External Link (`#link-repo`)
   - Active Target Summary Banner (module path, SHA-256 fingerprint, function count, line count)
   - `⚡ Run Hardening Pipeline` Quick Action Trigger (`#btn-scroll-to-hardening`)

2. **9 Core Workspace Tabs:**
   - **Tab 1: `📁 Mode A: Workspace & Upload`** (`#nav-mode-a`)  
     Target ingestion from workspace sample modules (`discount.py`, `banking.py`, `currency_converter.py`, etc.) or custom `.py` file drag-and-drop. AST function parser and code view.
   - **Tab 2: `✨ Mode B: AI Synthesis`** (`#nav-mode-b`)  
     Prompt-driven synthetic code generation with domain prompt chips (Order Book, Rate Limiter, Forex).
   - **Tab 3: `🌐 Mode C: GitHub Direct Import`** (`#nav-mode-c`)  
     Direct remote repository or file ingestion with dual subtabs: Single File URL and Full Repo Tree Explorer.
   - **Tab 4: `💥 Blast Radius & Call Graph`** (`#nav-blast`)  
     Interactive call graph visualizer, upstream caller / downstream callee tree hierarchy, impact risk scoring.
   - **Tab 5: `🔥 Hardening Lab & Results`** (`#nav-hardening`)  
     Primary execution cockpit: iteration control, score targets, progress monitor, cancellation control, mutant audit filter (All, Killed, Survived, Equivalent), unified diff viewer, test suite export.
   - **Tab 6: `🤖 Multi-Agent Wiretap`** (`#nav-wiretap`)  
     Real-time agent-to-agent message trace (Target Manager, Orchestrator, Sandbox Runner, Mutator).
   - **Tab 7: `📊 Observability Trace`** (`#nav-telemetry`)  
     Subsystem timing, hardware resource utilization, memory profiling, agent invocation logs.
   - **Tab 8: `⚡ Benchmarks & Ablation`** (`#nav-benchmark`)  
     Academic evaluation results, baseline vs hardened comparisons, mutation score gains, formatted vs raw markdown switch.
   - **Tab 9: `💾 Checkpoint Timeline & Diff`** (`#nav-checkpoints`)  
     Blackboard state snapshot manager, checkpoint restoration, JSON inspector, deterministic diff between checkpoint A and B.

### 3.2 Streamlit Hardening Workbench (`http://127.0.0.1:8501/`)
Organized as a multi-stage data app featuring:
- **Collapsible Sidebar:**
  - Execution mode radio (Auto Fallback, OpenRouter Cloud, Force Local Ollama, Force Cloud Gemini)
  - Masked API key inputs with visibility toggle
  - Foundation model dropdown (`gemini-3.6-flash`, `gemini-3.1-pro-preview`, `qwen2.5-coder:7b`)
  - Numeric sliders: Max Reflection Iterations (1–5), Target Mutation Score (50–100%)
  - Hardware & Provider status indicators
- **Main Workbench:**
  - Tab 1: `📁 Mode A: Pick / Upload Existing File`
  - Tab 2: `✨ Mode B: AI Module Synthesis`
  - Tab 3: `🌐 Mode C: GitHub Direct Import`
  - Tab 4: `🤖 Multi-Agent Inter-Communication & Wiretap`
  - Tab 5: `📊 Observability & Telemetry Trace`
  - Execution Area: `⚡ Run TestForge Autonomous Hardening` button with progress and metrics.

