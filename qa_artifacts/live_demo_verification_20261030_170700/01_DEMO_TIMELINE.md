# TESTFORGE — 7-MINUTE LIVE DEMONSTRATION TIMELINE
## Minute-by-Minute Operational Log, Script Actions & Captured Screenshot Evidence

**Demonstration Timestamp:** 2026-10-30T17:12:50+05:30  
**Target Target:** `samples/uploaded_logistics_engine.py` (240 lines)  
**Evidence Directory:** `qa_artifacts/live_demo_verification_20261030_170700/screenshots/`

---

## TIMELINE BREAKDOWN ACROSS 8 DEMONSTRATION STAGES

```
┌────────────────────────────────────────────────────────────────────────┐
│                        7-MINUTE DEMONSTRATION TIMELINE                 │
├─────────────┬──────────┬─────────────────────────────┬─────────────────┤
│ Time Window │ Duration │ Focus Area                  │ Evidence File   │
├─────────────┼──────────┼─────────────────────────────┼─────────────────┤
│ 00:00–00:45 │ 45s      │ Introduction & UI Layout    │ 01_project...   │
│ 00:45–01:30 │ 45s      │ Upload & AST Parsing        │ 02_upload...    │
│ 01:30–02:30 │ 60s      │ Call Graph & Wiretap        │ 03_blast...     │
│ 02:30–03:45 │ 75s      │ Hardening Pipeline Run      │ 05_hardening... │
│ 03:45–04:45 │ 60s      │ Test Studio Suite           │ 07_hardened...  │
│ 04:45–05:45 │ 60s      │ Mutants & AST Diff Modal    │ 08_mutants...   │
│ 05:45–06:30 │ 45s      │ A2A, FastMCP & Checkpoints  │ 11_a2a..., 12...│
│ 06:30–07:00 │ 30s      │ Final Verdict & Summary     │ 16_final...     │
└─────────────┴──────────┴─────────────────────────────┴─────────────────┘
```

---

### Stage 1: 00:00–00:45 — Project Introduction & Frontend Inspection
- **Objective:** Present the single-page application layout on FastAPI port `8000`, highlight system branding, navigation tabs, and system status badges.
- **Actions Executed:**
  1. Opened browser at `http://127.0.0.1:8000/`.
  2. Verified page title: `"TestForge — Autonomous Agentic Test Hardening"`.
  3. Inspected top navigation header with live WebSocket badge, A2A Card button, MCP Tools badge `( 4 )`, and Settings modal button.
  4. Verified Mode A Workspace & Upload view with built-in sample picker and custom upload dropzone.
- **Evidence:** [`screenshots/01_project_introduction_landing.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/01_project_introduction_landing.png)
- **Status:** **100% VERIFIED**

---

### Stage 2: 00:45–01:30 — Target Selection, Upload & AST Ingestion
- **Objective:** Ingest the realistic, multi-class target `samples/uploaded_logistics_engine.py` (240 lines) using the UI upload control and verify AST parsing.
- **Actions Executed:**
  1. Switched source radio from "Built-in Samples" to "Upload Custom .py" (`#radio-source-upload`).
  2. Uploaded `/Users/sourabh/TestForge/samples/uploaded_logistics_engine.py` into `#file-upload-input`.
  3. Verified upload preview updated dynamically to `"uploaded_logistics_engine.py (8.1 KB)"`.
  4. Clicked **Ingest Uploaded File** (`#btn-submit-upload`).
  5. Verified API request `POST /api/ingest/upload` returned HTTP 200.
  6. Verified AST Inspector dynamically populated:
     - Module: `samples.uploaded_uploaded_logistics_engine`
     - Classes: `ShippingTier, WarehouseInventory`
     - Functions: `calculate_item_discount, estimate_freight_cost, calculate_customs_duty, validate_tracking_number, compute_sla_deadline_hours, process_bulk_order`
- **Evidence:** [`screenshots/02_upload_and_ast_ingestion.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/02_upload_and_ast_ingestion.png)
- **Status:** **100% VERIFIED**

---

### Stage 3: 01:30–02:30 — AST Analysis, Call Graph & Context Sharing
- **Objective:** Demonstrate static call graph analysis and multi-agent context visualization prior to test synthesis.
- **Actions Executed:**
  1. Clicked **Blast Radius & Call Graph** tab (`button[data-tab='tab-blast']`).
  2. Inspected rendered call graph canvas visualizing caller-callee relationships among the 6 functions and 2 classes.
  3. Captured call graph topology screenshot.
  4. Clicked **Multi-Agent Wiretap** tab (`button[data-tab='tab-wiretap']`).
  5. Inspected active multi-agent timeline showing live WebSocket connection and registered agent nodes.
- **Evidence:** 
  - [`screenshots/03_blast_radius_and_call_graph.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/03_blast_radius_and_call_graph.png)
  - [`screenshots/04_multi_agent_wiretap_timeline.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/04_multi_agent_wiretap_timeline.png)
- **Status:** **100% VERIFIED**

---

### Stage 4: 02:30–03:45 — Multi-Agent Test Generation Execution
- **Objective:** Trigger the autonomous hardening pipeline, observe real-time agent handoffs, and monitor live execution.
- **Actions Executed:**
  1. Clicked **Hardening Lab & Results** tab (`button[data-tab='tab-hardening']`).
  2. Clicked primary action button **⚡ Run TestForge Autonomous Hardening** (`#btn-run-hardening`).
  3. Verified `#btn-run-hardening` transitioned to disabled state (`"⏳ Hardening Pipeline Active..."`).
  4. Verified `#btn-cancel-hardening` appeared with active cancellation capability.
  5. Observed in-flight progress box showing live stage indicator:
     `"Cycle 1/3 • GENERATING_TESTS - Google ADK Generator: Synthesizing candidate test assertions (Cycle 1/3)..."`
  6. Backend log confirmed: `TargetSpace` written -> `MutantSpace` written (258 mutants) -> `CriticSpace` analysis -> `SuiteSpace` synthesis.
- **Evidence:** 
  - [`screenshots/05_hardening_in_progress.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/05_hardening_in_progress.png)
  - [`screenshots/06_hardening_pipeline_completed.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/06_hardening_pipeline_completed.png)
- **Status:** **100% VERIFIED**

---

### Stage 5: 03:45–04:45 — Test Execution & Test Studio Inspection
- **Objective:** Verify execution of generated tests in the subprocess sandbox and inspect the synthesized Pytest code.
- **Actions Executed:**
  1. Scrolled to Test Studio code editor (`#test-hardened-code`).
  2. Verified generated suite contains granular scenarios: normal execution, boundary conditions, negative arguments, and `pytest.raises(ValueError)` exception handling.
  3. Exported raw test suite to [`artifacts/generated_logistics_tests.py`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/artifacts/generated_logistics_tests.py).
  4. Verified KPI Row 1: 11 tests generated, 11 tests executed, 11 tests passed, 0 failed (Verdict: `✅ PASSED`).
- **Evidence:** [`screenshots/07_hardened_test_studio_suite.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/07_hardened_test_studio_suite.png)
- **Status:** **100% VERIFIED**

---

### Stage 6: 04:45–05:45 — Mutation Testing & Mutant Inspector
- **Objective:** Audit the mutants table, exercise filtering controls, and open the AST unified diff inspector modal.
- **Actions Executed:**
  1. Clicked **KILLED** filter button (`button[data-filter='KILLED']`).
  2. Verified table filtered to killed mutants with green badges.
  3. Clicked **SURVIVED** filter button (`button[data-filter='SURVIVED']`).
  4. Verified table filtered to surviving mutants with amber badges.
  5. Clicked **ALL** filter button.
  6. Clicked on an individual mutant row to open the AST Unified Diff Viewer modal (`#mutant-diff-modal`).
  7. Inspected line-by-line unified diff snippet showing exact operator inversion.
  8. Clicked Close Modal (`#btn-close-mutant-modal`).
- **Evidence:** 
  - [`screenshots/08_mutants_table_killed.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/08_mutants_table_killed.png)
  - [`screenshots/09_mutants_table_survived.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/09_mutants_table_survived.png)
  - [`screenshots/10_mutant_diff_modal.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/10_mutant_diff_modal.png)
- **Status:** **100% VERIFIED**

---

### Stage 7: 05:45–06:30 — External Integrations, Protocols & Monitoring
- **Objective:** Demonstrate FastMCP tools, Linux Foundation A2A Agent Card, live telemetry traces, and SQLite checkpoint lineage.
- **Actions Executed:**
  1. Clicked **🤖 A2A Card** header button (`#btn-view-a2a`).
  2. Verified A2A Agent Card modal displayed valid JSON schema (protocol v0.3.0, skills: `unit-test-generation`, `mutation-critique`, `hardening-workflow`).
  3. Closed A2A modal (`#btn-close-a2a-modal`).
  4. Clicked **🔌 MCP Tools ( 4 )** header button (`#btn-view-mcp`).
  5. Verified FastMCP modal listed 4 registered tools: `list_directory`, `get_file_info`, `read_text_file`, `get_repository_info`.
  6. Closed MCP modal (`#btn-close-mcp-modal`).
  7. Clicked **Observability Trace** tab (`button[data-tab='tab-telemetry']`). Verified live telemetry table with timestamps, token counts, and durations.
  8. Clicked **Checkpoint Timeline & Diff** tab (`button[data-tab='tab-checkpoints']`). Verified point-in-time checkpoint stream from SQLite (`checkpoints.db`).
  9. Clicked Diff subtab (`#btn-subtab-diff`) to view checkpoint diff comparison.
- **Evidence:** 
  - [`screenshots/11_a2a_agent_card_modal.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/11_a2a_agent_card_modal.png)
  - [`screenshots/12_mcp_tools_modal.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/12_mcp_tools_modal.png)
  - [`screenshots/13_observability_trace.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/13_observability_trace.png)
  - [`screenshots/14_checkpoint_timeline.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/14_checkpoint_timeline.png)
  - [`screenshots/15_checkpoint_diff_viewer.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/15_checkpoint_diff_viewer.png)
- **Status:** **100% VERIFIED**

---

### Stage 8: 06:30–07:00 — Final Demonstration Results & Summary
- **Objective:** Review the final hardening verdict and present live accomplishments.
- **Actions Executed:**
  1. Returned to **Hardening Lab & Results** tab.
  2. Scrolled up to view the verdict banner.
  3. Verified terminal state recorded in SQLite: Checkpoint `chk_325953cc296f` with 258 mutants and 3 completed reflection cycles.
  4. Captured final summary screenshot.
- **Evidence:** [`screenshots/16_final_hardening_verdict.png`](file:///Users/sourabh/TestForge/qa_artifacts/live_demo_verification_20261030_170700/screenshots/16_final_hardening_verdict.png)
- **Status:** **100% VERIFIED**

