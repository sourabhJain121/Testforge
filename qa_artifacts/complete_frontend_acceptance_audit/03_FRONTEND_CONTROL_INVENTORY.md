# TestForge Frontend Control Inventory

**Audit Date:** 2026-10-30  
**Application Environments:**
- Primary Cockpit: FastAPI Single Page Application (`http://127.0.0.1:8000/`)
- Secondary Workbench: Streamlit Data Explorer (`http://127.0.0.1:8501/`)
**Auditor:** Antigravity Automated QA Suite

---

## 1. Inventory Summary

Across both web frontends, a total of **43 interactive controls, 14 view containers, and 4 modal dialogs** were discovered, cataloged, and verified:
- **FastAPI Cockpit (`:8000`):** 32 distinct interactive controls (9 top-level tabs, 4 status pills, 5 header action buttons, 3 modals, 4 sub-tabs, 7 action/filter buttons).
- **Streamlit Workbench (`:8501`):** 11 interactive widgets (1 sidebar radio, 2 key inputs, 1 model select, 2 sliders, 5 main tabs, 3 expanders, 1 primary action button).

---

## 2. FastAPI Modern Cockpit (`http://127.0.0.1:8000/`)

### 2.1 Navigation & Global Header Controls

| Control ID | Name | DOM Locator / Selector | Type | Initial State | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CTL-FA-001` | FastAPI Landing View | `body` | Container | Rendered | Main container hosting navbar, active target badge, tabs, and workspace panels. |
| `CTL-FA-002` | Hardware Profile Pill | `#pill-hardware` | Status Pill | Active | Displays OS architecture, physical core count, and memory (`arm64 10 cores 16GB`). |
| `CTL-FA-003` | Local Ollama Pill | `#pill-ollama` | Status Pill | Online | Live indicator for local offline model engine availability. |
| `CTL-FA-004` | Gemini Cloud Pill | `#pill-gemini` | Status Pill | Active | Live indicator for Google Gemini cloud model readiness. |
| `CTL-FA-005` | OpenRouter Pill | `#pill-openrouter` | Status Pill | Idle | Secondary cloud fallback tier status indicator. |
| `CTL-FA-006` | A2A Agent Card Button | `#btn-a2a-card` | Header Button | Visible | Opens modal for Agent-to-Agent (A2A) protocol card discovery and live RPC test. |
| `CTL-FA-008` | FastMCP Tools Button | `#btn-mcp-status` | Header Button | Visible | Opens modal displaying registered FastMCP stdio tool count and schema inspection. |
| `CTL-FA-010` | Settings Modal Toggle | `#btn-toggle-settings` | Header Button | Visible | Opens drawer for execution engine mode, model selection, and reflection sliders. |
| `CTL-FA-XL1` | Streamlit Cross-Link | `#btn-streamlit-link` | Anchor / Button | Visible | Direct header link opening Streamlit Secondary Data Workbench on port 8501. |
| `CTL-FA-XL2` | GitHub Repo Link | `#btn-github-repo` | Anchor / Button | Visible | External link to public source code repository. |
| `CTL-FA-CTA` | Scroll-to-Hardening | `#btn-scroll-to-hardening` | Action Button | Visible | Quick jump to Hardening Lab execution panel. |

### 2.2 Top-Level Navigation Tabs

| Control ID | Tab Name | DOM Locator / Selector | Type | Target Panel |
| :--- | :--- | :--- | :--- | :--- |
| `CTL-FA-012` | Mode A: Workspace & Upload | `#nav-mode-a` | Tab Button | `#tab-mode-a` |
| `CTL-FA-013` | Mode B: AI Synthesis | `#nav-mode-b` | Tab Button | `#tab-mode-b` |
| `CTL-FA-014` | Mode C: GitHub Direct Import | `#nav-mode-c` | Tab Button | `#tab-mode-c` |
| `CTL-FA-015` | Blast Radius & Call Graph | `#nav-blast` | Tab Button | `#tab-blast` |
| `CTL-FA-016` | Hardening Lab & Results | `#nav-hardening` | Tab Button | `#tab-hardening` |
| `CTL-FA-017` | Multi-Agent Wiretap | `#nav-wiretap` | Tab Button | `#tab-wiretap` |
| `CTL-FA-018` | Observability Trace | `#nav-telemetry` | Tab Button | `#tab-telemetry` |
| `CTL-FA-019` | Benchmarks & Ablation | `#nav-benchmark` | Tab Button | `#tab-benchmark` |
| `CTL-FA-020` | Checkpoints & Timeline | `#nav-checkpoints` | Tab Button | `#tab-checkpoints` |

### 2.3 Panel Controls & Form Elements

| Control ID | Name | DOM Locator / Selector | Type | Functionality |
| :--- | :--- | :--- | :--- | :--- |
| `CTL-FA-021` | Sample Selector | `#sample-file-select` | Select Dropdown | Selects built-in Python modules (`discount.py`, `banking.py`, etc.). |
| `CTL-FA-022` | Load Sample Button | `#btn-load-sample` | Action Button | Triggers `/api/ingest/sample` and populates AST viewer. |
| `CTL-FA-023` | Git Diff-Aware Toggle | `#toggle-git-diff` | Checkbox | Restricts mutation generation to uncommitted Git modified lines. |
| `CTL-FA-024` | Prompt Preset Chips | `.prompt-chip` | Button Group | Fills Mode B synthesis textarea with domain test specifications. |
| `CTL-FA-025` | Mode C Repo Chips | `.repo-chip` | Button Group | Populates Mode C repository input with target URLs. |
| `CTL-FA-026` | Refresh Wiretap Button | `#btn-refresh-wiretap` | Action Button | Queries `/api/wiretap` to refresh agent handoff sequence. |
| `CTL-FA-027` | Refresh Telemetry Button | `#btn-refresh-telemetry` | Action Button | Queries `/api/telemetry` to refresh token usage and event logs. |
| `CTL-FA-028` | Benchmark Markdown Toggle | `#btn-bench-md-raw` / `#btn-bench-md-rendered` | Button Group | Toggles ablation study report between rendered HTML and raw Markdown. |
| `CTL-FA-030` | Refresh Checkpoints | `#btn-refresh-checkpoints` | Action Button | Queries `/api/checkpoints` for persisted SQLite snapshots. |
| `CTL-FA-031` | Checkpoint Diff Sub-tab | `#btn-subtab-diff` | Sub-tab Button | Displays side-by-side AST / state diff for two selected checkpoints. |
| `CTL-FA-032` | Checkpoint JSON Sub-tab | `#btn-subtab-json` | Sub-tab Button | Displays formatted raw JSON payload of the active checkpoint snapshot. |

---

## 3. Streamlit Data Workbench (`http://127.0.0.1:8501/`)

### 3.1 Sidebar System Configuration

| Control ID | Name | DOM Locator / Selector | Type | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CTL-ST-002` | Execution Mode Radio | `div[data-testid='stRadio']` | Radio Group | Auto | Switches between Auto, OpenRouter Cloud, Force Local Ollama, and Force Cloud. |
| `CTL-ST-KEY1` | Gemini API Key | `input[type='password']` | Text Input | Pre-filled | Allows overriding Gemini API Key at runtime. |
| `CTL-ST-KEY2` | OpenRouter Key | `input[type='password']` | Text Input | Empty | Allows setting secondary fallback key. |
| `CTL-ST-MOD` | Foundation Model | `div[data-baseweb='select']` | Dropdown | `gemini-3.6-flash` | Selects primary generation model. |
| `CTL-ST-ITER` | Max Reflection Iterations | `div[data-testid='stSlider']` | Slider | 3 | Sets upper bound on agentic critique cycles (1-5). |
| `CTL-ST-MUT` | Target Mutation Score | `div[data-testid='stSlider']` | Slider | 85.0% | Sets stopping mutation threshold (50%-100%). |
| `CTL-ST-003` | Hardware Profile Card | `div[data-testid='stMetric']` | Metric Badge | `arm64 10 Cores` | Real-time Apple Silicon resource diagnostics. |

### 3.2 Main Workspace Tabs & Expanders

| Control ID | Name | DOM Locator / Selector | Type | Functionality |
| :--- | :--- | :--- | :--- | :--- |
| `CTL-ST-004` | Mode A Tab | `button[data-baseweb='tab']:nth-of-type(1)` | Tab | Displays Workspace Sample selection and file upload. |
| `CTL-ST-005` | Mode B Tab | `button[data-baseweb='tab']:nth-of-type(2)` | Tab | Displays AI Module Synthesis prompt input. |
| `CTL-ST-006` | Mode C Tab | `button[data-baseweb='tab']:nth-of-type(3)` | Tab | Displays GitHub direct import input and fetch action. |
| `CTL-ST-007` | Wiretap Tab | `button[data-baseweb='tab']:nth-of-type(4)` | Tab | Displays multi-agent handoff inspector with search & filters. |
| `CTL-ST-008` | Telemetry Tab | `button[data-baseweb='tab']:nth-of-type(5)` | Tab | Displays live telemetry traces and token consumption. |
| `CTL-ST-009` | Source Expander | `details summary:has-text('View Ingested')` | Expander | Collapsible panel showing syntax-highlighted Python target source. |
| `CTL-ST-010` | Blast Radius Expander | `details summary:has-text('Blast Radius')` | Expander | Collapsible panel showing call graph and blast metrics. |
| `CTL-ST-011` | Run Hardening CTA | `button:has-text('Run TestForge')` | Primary Button | Triggers in-process autonomous multi-agent hardening pipeline. |

