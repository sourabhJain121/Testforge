# TestForge Frontend Interaction Test Results

**Audit Date:** 2026-10-30  
**Test Harness:** Automated Playwright Headless Browser via `agent-browser`  
**Total Interactive Controls Tested:** 43  
**Passing Controls:** 43 (100%)  
**Defective Controls:** 0 (after targeted remediation)

---

## 1. FastAPI Dashboard Interaction Test Log

| Control ID | Control Tested | Action Performed | Resulting State / DOM Change | Backend Request / Status | Status | Screenshot Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CTL-FA-001` | Landing View | Navigate `http://127.0.0.1:8000/` | Full cockpit rendered with active target `samples.discount` | `GET /` -> `200` | **PASS** | `fastapi_01_landing.png` |
| `CTL-FA-002` | Hardware Pill | Hover & Inspect badge | Shows `Darwin arm64 (10 cores, 16GB)` | `GET /api/status` -> `200` | **PASS** | `fastapi_02_status_pills.png` |
| `CTL-FA-003` | Ollama Pill | Inspect indicator dot | Shows `Ollama (Online)` with green pulse | `GET /api/status` -> `200` | **PASS** | `fastapi_02_status_pills.png` |
| `CTL-FA-004` | Gemini Pill | Inspect indicator dot | Shows `Gemini (Active)` with green pulse | `GET /api/status` -> `200` | **PASS** | `fastapi_02_status_pills.png` |
| `CTL-FA-005` | OpenRouter Pill | Inspect indicator dot | Shows `OpenRouter (Idle)` with gray dot | `GET /api/status` -> `200` | **PASS** | `fastapi_02_status_pills.png` |
| `CTL-FA-006` | A2A Card Button | Click `#btn-a2a-card` | Modal opens, renders live A2A AgentCard JSON payload | `GET /.well-known/agent-card.json` -> `200` | **PASS** | `fastapi_03_a2a_modal_open.png` |
| `CTL-FA-007` | A2A Run Test | Click `#btn-run-a2a-test` | Inter-agent ping dispatched; status `OPERATIONAL` in 1.4ms | `POST /api/a2a/test` -> `200` | **PASS** | `fastapi_04_a2a_test_run.png` |
| `CTL-FA-008` | MCP Status Button | Click `#btn-mcp-status` | Modal opens, lists 4 tools across 2 servers | `GET /api/mcp/status` -> `200` | **PASS** | `fastapi_05_mcp_modal_open.png` |
| `CTL-FA-009` | MCP Run Test | Click `#btn-run-mcp-test` | `list_directory` invoked over stdio; verified confinement | `POST /api/mcp/test` -> `200` | **PASS** | `fastapi_06_mcp_test_run.png` |
| `CTL-FA-010` | Settings Button | Click `#btn-toggle-settings` | Drawer opens with configuration sliders and engine select | DOM toggle | **PASS** | `fastapi_07_settings_modal_open.png` |
| `CTL-FA-011` | Engine Mode Select | Change to `local` | Dropdown value updated to Offline Ollama mode | DOM change | **PASS** | `fastapi_07_settings_modal_open.png` |
| `CTL-FA-012` | Mode A Tab | Click `#nav-mode-a` | Displays workspace targets, sample picker, and AST viewer | DOM toggle | **PASS** | `fastapi_08_tab_mode_a.png` |
| `CTL-FA-013` | Mode B Tab | Click `#nav-mode-b` | Displays specification prompt area and template chips | DOM toggle | **PASS** | `fastapi_09_tab_mode_b.png` |
| `CTL-FA-014` | Mode C Tab | Click `#nav-mode-c` | Displays GitHub repo URL input and branch selector | DOM toggle | **PASS** | `fastapi_10_tab_mode_c.png` |
| `CTL-FA-015` | Blast Radius Tab | Click `#nav-blast` | Displays interactive Mermaid dependency call graph | DOM toggle | **PASS** | `fastapi_11_tab_blast.png` |
| `CTL-FA-016` | Hardening Tab | Click `#nav-hardening` | Displays execution telemetry, mutant filters, diff viewer | DOM toggle | **PASS** | `fastapi_12_tab_hardening.png` |
| `CTL-FA-017` | Wiretap Tab | Click `#nav-wiretap` | Displays inter-agent message trajectory and audit log | DOM toggle | **PASS** | `fastapi_13_tab_wiretap.png` |
| `CTL-FA-018` | Telemetry Tab | Click `#nav-telemetry` | Displays token gauges, call latency, and trace events | DOM toggle | **PASS** | `fastapi_14_tab_telemetry.png` |
| `CTL-FA-019` | Benchmarks Tab | Click `#nav-benchmark` | Displays ablation comparison charts and markdown viewer | DOM toggle | **PASS** | `fastapi_15_tab_benchmark.png` |
| `CTL-FA-020` | Checkpoints Tab | Click `#nav-checkpoints` | Displays SQLite checkpoints timeline and diff inspector | DOM toggle | **PASS** | `fastapi_16_tab_checkpoints.png` |
| `CTL-FA-021` | Sample Selector | Select `samples/banking.py` | Updates dropdown selection | DOM change | **PASS** | `fastapi_17_banking_sample_loaded.png` |
| `CTL-FA-022` | Load Sample Button | Click `#btn-load-sample` | Loads `banking.py`, extracts `transfer`, `deposit` AST nodes | `POST /api/ingest/sample` -> `200` | **PASS** | `fastapi_17_banking_sample_loaded.png` |
| `CTL-FA-023` | Git Diff Toggle | Check `#toggle-git-diff` | Activates git diff targeted line filtering mode | DOM change | **PASS** | `fastapi_18_git_diff_toggled.png` |
| `CTL-FA-024` | Mode B Prompt Chip | Click Order Book Chip | Injects prompt text into specification textarea | DOM change | **PASS** | `fastapi_19_mode_b_chip_clicked.png` |
| `CTL-FA-025` | Mode C Repo Chip | Click TestForge Chip | Injects repo URL into GitHub ingestion field | DOM change | **PASS** | `fastapi_20_mode_c_chip_clicked.png` |
| `CTL-FA-026` | Refresh Wiretap | Click `#btn-refresh-wiretap` | Pulls latest multi-agent handoff records | `GET /api/wiretap` -> `200` | **PASS** | `fastapi_21_wiretap_refreshed.png` |
| `CTL-FA-027` | Refresh Telemetry | Click `#btn-refresh-telemetry` | Pulls live token usage and event records | `GET /api/telemetry` -> `200` | **PASS** | `fastapi_22_telemetry_refreshed.png` |
| `CTL-FA-028` | Raw Markdown Toggle | Click `#btn-bench-md-raw` | Switches benchmark display to raw Markdown codeblock | DOM toggle | **PASS** | `fastapi_23_bench_raw_toggle.png` |
| `CTL-FA-029` | Formatted MD Toggle | Click `#btn-bench-md-rendered` | Switches benchmark display back to styled HTML table | DOM toggle | **PASS** | `fastapi_23_bench_raw_toggle.png` |
| `CTL-FA-030` | Refresh Checkpoints | Click `#btn-refresh-checkpoints` | Queries SQLite blackboard checkpoints | `GET /api/checkpoints` -> `200` | **PASS** | `fastapi_24_cp_refreshed.png` |
| `CTL-FA-031` | Checkpoint Diff Tab | Click `#btn-subtab-diff` | Displays side-by-side AST / state diff view | DOM toggle | **PASS** | `fastapi_25_cp_subtab_diff.png` |
| `CTL-FA-032` | Checkpoint JSON Tab | Click `#btn-subtab-json` | Displays full JSON snapshot object | DOM toggle | **PASS** | `fastapi_26_cp_subtab_json.png` |
| `CTL-FA-033` | Streamlit Header Link | Click `#btn-streamlit-link` | Opens Streamlit Secondary Workbench in new tab | Link navigation | **PASS** | `fastapi_header_with_crosslink.png` |

---

## 2. Streamlit Workbench Interaction Test Log

| Control ID | Control Tested | Action Performed | Resulting State / DOM Change | Backend Execution | Status | Screenshot Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CTL-ST-001` | Landing View | Navigate `http://127.0.0.1:8501/` | Streamlit app loads in <2s with primary cockpit banner | In-process Streamlit | **PASS** | `streamlit_01_landing.png` |
| `CTL-ST-002` | Sidebar Config | Inspect sidebar widgets | Displays mode radio, keys, model, iterations slider | Streamlit Session | **PASS** | `streamlit_02_sidebar.png` |
| `CTL-ST-003` | Hardware Profile | Inspect metrics | Displays Darwin arm64, 10 Cores, 16GB RAM | In-process OS Probe | **PASS** | `streamlit_02_sidebar.png` |
| `CTL-ST-004` | Mode A Tab | Click Tab 1 | Displays workspace sample picker and file uploader | Streamlit Session | **PASS** | `streamlit_03_tab_mode_a.png` |
| `CTL-ST-005` | Mode B Tab | Click Tab 2 | Displays AI synthesis prompt textarea | Streamlit Session | **PASS** | `streamlit_04_tab_mode_b.png` |
| `CTL-ST-006` | Mode C Tab | Click Tab 3 | Displays GitHub URL input and Fetch button | Streamlit Session | **PASS** | `streamlit_05_tab_mode_c.png` |
| `CTL-ST-007` | Wiretap Tab | Click Tab 4 | Displays agent handoffs with iteration / agent filters | Streamlit Session | **PASS** | `streamlit_06_tab_wiretap.png` |
| `CTL-ST-008` | Telemetry Tab | Click Tab 5 | Displays token metrics and collapsible trace logs | Streamlit Session | **PASS** | `streamlit_07_tab_telemetry.png` |
| `CTL-ST-009` | Source Expander | Click "View Ingested Code" | Expands to display syntax-highlighted source code | Streamlit DOM | **PASS** | `streamlit_08_source_expander.png` |
| `CTL-ST-010` | Blast Expander | Click "Blast Radius" | Expands to display call graph & dependency metrics | Streamlit DOM | **PASS** | `streamlit_09_blast_expander.png` |
| `CTL-ST-011` | Primary CTA Button | Inspect Hardening Button | Full-width button rendered with prominent styling | Streamlit DOM | **PASS** | `streamlit_10_primary_action.png` |
| `CTL-ST-012` | Cockpit Link Banner | Inspect info callout | Displays banner pointing users to FastAPI port 8000 | Streamlit DOM | **PASS** | `streamlit_with_cockpit_banner.png` |

