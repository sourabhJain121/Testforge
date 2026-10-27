# Final Live Acceptance Report: Visible Browser Playground, UI-to-Backend Debugging & Automated Regression

**Audit Run**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Date**: 2026-10-27  
**Execution Environment**: macOS Apple Silicon (10 Cores, 16GB RAM)  
**Browser**: Google Chrome v156.0.8078.48 (Official Build, arm64, Headed/Visible Window)  
**Backend**: FastAPI / Uvicorn listening on `http://127.0.0.1:8000/`  

---

## 1. Final Verdict

### **PASS — VERIFIED FOR TESTED SCOPE**

The application was opened, driven, and visibly verified in a real headed Google Chrome browser. All primary objectives were accomplished:
- Headed Chrome was launched and kept active and visible on the user's screen.
- The defect where frontend KPI cards showed `0.0%`, `0 / 20`, or `⚪ NONE` was reproduced, isolated to a field name schema mismatch in `frontend/app.js`, repaired, and verified.
- Five real Git-tracked sample source files were processed through the actual visible UI.
- All rendered DOM values were compared against authoritative backend `/api/harden/status/{job_id}` responses, achieving **100% data parity (`MATCH`)**.
- Cooperative job cancellation and empty target guards were tested and verified.
- Full regression passed: **428 tests passed, 0 failed** (`FULL_TEST_RUN.log`).
- The application remains **open and active in the visible browser** on the completed hardening demonstration view.

---

## 2. Browser & Launch Configuration

1. **Browser Application**: Google Chrome v156.0.8078.48 (arm64)
2. **Launch Flags**:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --remote-debugging-port=9222 \
     --user-data-dir="/tmp/chrome_testforge_debug" \
     "http://127.0.0.1:8000/"
   ```
3. **Window Management**:
   The window was brought to the foreground of the macOS workspace via `osascript -e 'tell application "Google Chrome" to activate'` before every major workflow.
4. **Interaction Mode**: Headed Chrome DevTools Protocol automation controlling real mouse and event dispatches against the visible DOM.

---

## 3. Tested Source Files & Live Verification Results

| # | Source File | Active Job ID | Duration | Mutants (Gen/Kill/Surv) | Verified Mutation Score | Line Coverage | Baseline Verdict | Parity Status | Screenshot |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `samples/discount.py` | `7ece683e` | 15.0s | 19 / 12 / 7 | **63.2%** | 100.0% (10/10) | 🟢 ALL PASSED | **MATCH** | `01_discount_hardening_complete.png` |
| **2** | `samples/banking.py` | `c72bfc10` | 17.1s | 23 / 12 / 11 | **52.2%** | 90.0% (9/10) | 🟢 ALL PASSED | **MATCH** | `02_banking_hardening_complete.png` |
| **3** | `samples/inventory_pricing.py` | `2d7e1089` | 23.0s | 37 / 17 / 20 | **46.0%** | 71.4% (15/21) | 🟢 ALL PASSED | **MATCH** | `03_inventory_pricing_hardening_complete.png` |
| **4** | `samples/state_machine.py` | `6abda83d` | 35.4s | 57 / 12 / 45 | **21.1%** | 64.3% (9/14) | 🟢 ALL PASSED | **MATCH** | `04_state_machine_hardening_complete.png` |
| **5** | `samples/rate_limiter.py` | `bf3e4392` | 23.1s | 38 / 16 / 22 | **42.1%** | 81.8% (9/11) | 🟢 ALL PASSED | **MATCH** | `05_rate_limiter_hardening_complete.png` |

---

## 4. Defect Root Cause & Applied Repairs

### Defect TF-DEF-005: KPI Metric Cards Blank / 0.0% Display
- **Symptom**: In previous audits, backend mutation scores (e.g. 63.16%) were generated, but frontend cards `#kpi-mut-score`, `#kpi-mut-kill`, and `#kpi-base-verdict` remained zeroed.
- **Root Cause**: Field name mismatch between backend `TestForgeState` and frontend `frontend/app.js`:
  - Score: backend sent `final_mutation_score`; frontend checked `mutation_score`.
  - Mutants: backend sent `killed_mutants` / `survived_mutants` in `history` records; frontend checked `mutants_killed` in `iteration_history`.
  - Baseline: backend sent flat fields (`baseline_tests_passed`, `baseline_passed`); frontend checked `baseline_run.tests_passed`.
- **Applied Fix**:
  1. Updated `frontend/app.js` (`renderHardeningResults` & `renderHistoryTable`) with null-coalescing lookups across both canonical and alias fields.
  2. Updated `server.py` (`job_record["final_state"] = state_dict`) to inject bidirectional alias keys (`mutation_score`, `hardening_status`, `iteration_history`, `baseline_coverage`, `baseline_run`).
  3. Exposed `window.__testforge` helpers for automated verification and telemetry inspection.

---

## 5. Negative & Secondary Control Verification

1. **Job Cancellation**:
   - Job `1bd95ca1` was launched on `discount.py` and cancelled mid-run via `#btn-cancel-hardening`.
   - UI cleanly halted workers, preserved partial data, and rendered `🛑 Hardening Cancelled`.
   - Backend transitioned to `CANCELLED`.
   - Evidence: `06_cancellation_state.png`.
2. **Empty Target Guard**:
   - Attempting execution without loaded code displayed a warning toast and prevented empty job creation.
3. **Secondary Controls Tested**:
   - A2A Agent Card Drawer (`#btn-a2a-card`) -> `07_a2a_drawer.png`
   - MCP Tools Status Drawer (`#btn-mcp-status`) -> `08_mcp_drawer.png`
   - Settings Drawer (`#btn-toggle-settings`) -> `09_settings_drawer.png`
   - Wiretap Real-Time Message Stream Tab (`#nav-wiretap`) -> `10_wiretap_view.png`
   - Telemetry Traces Tab (`#nav-telemetry`) -> `11_telemetry_view.png`
   - Benchmark Tab (`#nav-benchmark`) -> `12_benchmark_view.png`
   - Checkpoints Tab (`#nav-checkpoints`) -> `13_checkpoints_view.png`

---

## 6. Full Regression Suite Results

Command: `.venv-release/bin/python -m pytest tests/ -q`
- **Result**: **428 passed, 0 failed** in 254.65s (04m 14s)
- **Exit Code**: 0
- **Log Path**: `FULL_TEST_RUN.log`

---

## 7. Artifact Index

All generated audit evidence is stored under `qa_artifacts/visible_browser_playground_20261027_083200/`:
- `LIVE_DEMO_RUNBOOK.md` — Complete instructions and execution sequence
- `LIVE_UI_SOURCE_FILE_RESULTS.csv` — Per-file UI execution results
- `LIVE_UI_JOB_METRICS.csv` — Comprehensive execution telemetry
- `UI_BACKEND_METRIC_PARITY.csv` — Field-by-field parity cross-check matrix
- `LIVE_UI_ERROR_CASES.csv` — Cancellation and guard validation
- `LIVE_UI_BACKEND_CROSSCHECK.md` — Mathematical recomputation and data parity review
- `DEFECT_REGISTER.csv` & `DEFECT_REPAIR_LOG.md` — Defect tracking and remediation
- `FINAL_REGRESSION_RESULTS.md` & `FULL_TEST_RUN.log` — Pytest suite execution
- `FINAL_BROWSER_CONSOLE.log` & `FINAL_BACKEND_LOG_REVIEW.md` — Runtime logs review
- `FINAL_GIT_STATUS.txt` & `GIT_INTEGRITY_REPORT.md` — Repository integrity verification
- `screenshots/00_baseline_dashboard.png` through `screenshots/14_final_completed_hardening_demonstration.png`

---

## 8. Live Demonstration Status & Handoff

The application is currently **OPEN and ACTIVE** in Google Chrome on your screen:
- **URL**: `http://127.0.0.1:8000/`
- **Current View**: Autonomous Hardening Lab (`#tab-hardening`)
- **Rendered Results**: Completed Hardening Run showing verified mutation metrics (**63.2% score**, 12 killed, 7 survived, 100% coverage, 🟢 ALL PASSED baseline verdict)
- **Backend Process**: Listening on `http://127.0.0.1:8000/` (PID 17886)
