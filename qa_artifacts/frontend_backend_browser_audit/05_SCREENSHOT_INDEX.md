# 05 — Master Screenshot Evidence Index

**TestForge Master Frontend, Backend & Browser Acceptance Audit**  
**Evidence Repository:** `qa_artifacts/frontend_backend_browser_audit/screenshots/`  
**Total Screenshots Captured:** 75 (67 Standard Views + 8 Responsive Layouts)

---

## 1. Master Evidence Index

| Filename | Page / Component | State / Action Captured | Test Case ID | Status |
| :--- | :--- | :--- | :--- | :--- |
| `01_fastapi_dashboard_initial.png` | FastAPI Dashboard | Initial load complete overview | TC-DASH-001 | PASS |
| `01_fastapi_dashboard_initial_full.png` | FastAPI Dashboard | Full-page vertical scroll capture | TC-DASH-001 | PASS |
| `01_fastapi_dashboard_initial_viewport.png` | FastAPI Dashboard | Initial viewport (1440x900) | TC-DASH-001 | PASS |
| `02_a2a_button_before.png` | Header Bar | A2A Card button prior to click | TC-DASH-002 | PASS |
| `02_a2a_modal_opened.png` | A2A Modal | Modal open displaying agent card JSON | TC-DASH-002 | PASS |
| `02_a2a_modal_tested.png` | A2A Modal | After clicking "Run Test Action" (ping/pong) | TC-DASH-002 | PASS |
| `02_a2a_modal_closed.png` | Dashboard Header | After clicking Close modal button | TC-DASH-002 | PASS |
| `03_mcp_button_before.png` | Header Bar | MCP button prior to click | TC-DASH-003 | PASS |
| `03_mcp_modal_opened.png` | MCP Modal | Modal open displaying 4 FastMCP tools | TC-DASH-003 | PASS |
| `03_mcp_modal_tested.png` | MCP Modal | After clicking "Run MCP Test Action" (200 OK)| TC-DASH-003 | PASS |
| `03_mcp_modal_closed.png` | Dashboard Header | After dismissing MCP modal | TC-DASH-003 | PASS |
| `04_settings_button_before.png` | Header Bar | Settings button prior to click | TC-DASH-004 | PASS |
| `04_settings_modal_opened.png` | Settings Drawer | Settings drawer open with API key inputs | TC-DASH-004 | PASS |
| `04_settings_modal_closed.png` | Dashboard Header | After closing settings drawer | TC-DASH-004 | PASS |
| `05_mode_a_sample_select_before.png`| Mode A Workspace | Dropdown open selecting sample module | TC-DASH-005 | PASS |
| `05_mode_a_sample_loaded_banking.png`| Mode A Workspace | After loading banking.py & AST inspection | TC-DASH-005 | PASS |
| `05_mode_a_git_diff_toggled.png` | Mode A Workspace | Git Diff targeted hardening switch toggled | TC-DASH-005 | PASS |
| `06_tab_mode_b_before.png` | Tab Bar | Tab Mode B prior to activation | TC-DASH-006 | PASS |
| `06_tab_mode_b_opened.png` | Mode B Synthesis | Mode B workspace active with prompt chips | TC-DASH-006 | PASS |
| `06_tab_mode_b_chip_clicked.png` | Mode B Synthesis | After clicking "Order Book Engine" chip | TC-DASH-006 | PASS |
| `07_tab_mode_c_before.png` | Tab Bar | Tab Mode C prior to activation | TC-DASH-007 | PASS |
| `07_tab_mode_c_opened.png` | Mode C GitHub | Mode C workspace active (Single File subtab)| TC-DASH-007 | PASS |
| `07_tab_mode_c_repo_tree_subtab.png`| Mode C GitHub | Switched to "Repository Tree Exploration" subtab| TC-DASH-007 | PASS |
| `07_tab_mode_c_repo_chip_clicked.png`| Mode C GitHub | After clicking repo chip `sourabhJain121/Testforge`| TC-DASH-007 | PASS |
| `08_tab_blast_before.png` | Tab Bar | Tab Blast Radius prior to click | TC-DASH-008 | PASS |
| `08_tab_blast_opened.png` | Blast Radius Tab | Visual call graph canvas & dependency trees | TC-DASH-008 | PASS |
| `09_tab_hardening_before.png` | Tab Bar | Tab Hardening Lab prior to click | TC-DASH-009 | PASS |
| `09_tab_hardening_opened.png` | Hardening Lab | Hardening cockpit with score rings & KPIs | TC-DASH-009 | PASS |
| `09_tab_hardening_filter_killed.png` | Hardening Lab | Mutant table filtered to "KILLED" | TC-DASH-009 | PASS |
| `10_tab_wiretap_before.png` | Tab Bar | Tab Wiretap prior to click | TC-DASH-010 | PASS |
| `10_tab_wiretap_opened.png` | Wiretap Tab | Agent communication log stream | TC-DASH-010 | PASS |
| `10_tab_wiretap_refreshed.png` | Wiretap Tab | After clicking "Refresh Wiretap" | TC-DASH-010 | PASS |
| `11_tab_telemetry_before.png` | Tab Bar | Tab Telemetry prior to click | TC-DASH-011 | PASS |
| `11_tab_telemetry_opened.png` | Telemetry Tab | Observability metrics, CPU, memory, latencies| TC-DASH-011 | PASS |
| `11_tab_telemetry_refreshed.png`| Telemetry Tab | After clicking "Refresh Telemetry" | TC-DASH-011 | PASS |
| `12_tab_benchmark_before.png` | Tab Bar | Tab Benchmark prior to click | TC-DASH-012 | PASS |
| `12_tab_benchmark_opened.png` | Benchmark Tab | Initial benchmark academic tables | TC-DASH-012 | PASS |
| `12_tab_benchmark_refreshed.png`| Benchmark Tab | After clicking "Refresh Results" | TC-DASH-012 | PASS |
| `12_tab_benchmark_raw_md.png` | Benchmark Tab | View toggled to Raw Markdown | TC-DASH-012 | PASS |
| `12_tab_benchmark_formatted_md.png`| Benchmark Tab | View toggled to Formatted Markdown tables | TC-DASH-012 | PASS |
| `13_tab_checkpoints_before.png` | Tab Bar | Tab Checkpoints prior to click | TC-DASH-013 | PASS |
| `13_tab_checkpoints_opened.png` | Checkpoints Tab | Snapshot manager & timeline | TC-DASH-013 | PASS |
| `13_tab_checkpoints_refreshed.png`| Checkpoints Tab | After clicking "Refresh Checkpoints" | TC-DASH-013 | PASS |
| `13_tab_checkpoints_subtab_detail.png`| Checkpoints Tab | Structured inspector subtab view | TC-DASH-013 | PASS |
| `13_tab_checkpoints_subtab_diff.png` | Checkpoints Tab | Deterministic diff subtab view | TC-DASH-013 | PASS |
| `13_tab_checkpoints_subtab_json.png` | Checkpoints Tab | Raw snapshot JSON subtab view | TC-DASH-013 | PASS |
| `20_streamlit_initial_viewport.png` | Streamlit App | Initial Streamlit viewport (1440x900) | TC-ST-001 | PASS |
| `20_streamlit_initial_full.png` | Streamlit App | Full-page vertical capture of Streamlit app | TC-ST-001 | PASS |
| `21_streamlit_mode_a_before.png` | Streamlit Mode A | Prior to clicking Load Workspace Sample | TC-ST-002 | PASS |
| `21_streamlit_mode_a_sample_loaded.png`| Streamlit Mode A | After loading sample: AST & code expander | TC-ST-002 | PASS |
| `22_streamlit_tab_mode_b.png` | Streamlit Tabs | Mode B AI Module Synthesis tab | TC-ST-003 | PASS |
| `23_streamlit_tab_mode_c.png` | Streamlit Tabs | Mode C GitHub Direct Import tab | TC-ST-004 | PASS |
| `24_streamlit_tab_wiretap.png` | Streamlit Tabs | Multi-Agent Inter-Communication & Wiretap | TC-ST-005 | PASS |
| `25_streamlit_tab_observability.png`| Streamlit Tabs | Observability & Telemetry Trace tab | TC-ST-006 | PASS |
| `30_swagger_docs_viewport.png` | Swagger UI | Swagger UI initial viewport | TC-SWAG-001 | PASS |
| `30_swagger_docs_full.png` | Swagger UI | Complete vertical scroll of 46 endpoints | TC-SWAG-001 | PASS |
| `31_swagger_healthz_expanded.png` | Swagger UI | Endpoint `/healthz` accordion expanded | TC-SWAG-001 | PASS |
| `31_swagger_healthz_executed.png` | Swagger UI | Response 200 OK after clicking "Execute" | TC-SWAG-001 | PASS |
| `32_redoc_initial.png` | ReDoc | Full ReDoc documentation scroll | TC-REDOC-001 | PASS |
| `40_hardening_workflow_before_start.png`| Hardening Lab | Pre-execution state of Hardening Lab | TC-DASH-WORKFLOW-001 | PASS |
| `41_hardening_workflow_started_running.png`| Hardening Lab | Running state with progress bar & cancel button| TC-DASH-WORKFLOW-001 | PASS |
| `42_hardening_workflow_cancelled.png`| Hardening Lab | Cancelled state with safe termination toast | TC-DASH-WORKFLOW-001 | PASS |
| `50_streamlit_workflow_before_load.png`| Streamlit App | Pre-sample load state | TC-ST-WORKFLOW-001 | PASS |
| `51_streamlit_workflow_after_load.png`| Streamlit App | Post-sample load state with code tree | TC-ST-WORKFLOW-001 | PASS |

---

## 2. Responsive Viewport Evidence Index

| Filename | Interface | Viewport Size | Device Category | Status |
| :--- | :--- | :--- | :--- | :--- |
| `responsive/fastapi_dashboard_desktop_1440x900.png` | Web Dashboard | 1440 × 900 | Desktop Standard | PASS |
| `responsive/fastapi_dashboard_laptop_1280x800.png` | Web Dashboard | 1280 × 800 | Laptop Compact | PASS |
| `responsive/fastapi_dashboard_tablet_768x1024.png` | Web Dashboard | 768 × 1024 | Tablet Portrait | PASS |
| `responsive/fastapi_dashboard_mobile_390x844.png` | Web Dashboard | 390 × 844 | Mobile (iPhone 14/15) | PASS |
| `responsive/streamlit_desktop_1440x900.png` | Streamlit App | 1440 × 900 | Desktop Standard | PASS |
| `responsive/streamlit_laptop_1280x800.png` | Streamlit App | 1280 × 800 | Laptop Compact | PASS |
| `responsive/streamlit_tablet_768x1024.png` | Streamlit App | 768 × 1024 | Tablet Portrait | PASS |
| `responsive/streamlit_mobile_390x844.png` | Streamlit App | 390 × 844 | Mobile (iPhone 14/15) | PASS |

