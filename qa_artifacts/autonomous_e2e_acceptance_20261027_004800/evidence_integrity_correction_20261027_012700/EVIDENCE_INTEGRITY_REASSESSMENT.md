# TestForge — Evidence Integrity Reassessment & Correction Report

**Audit Session:** `autonomous_e2e_acceptance_20261027_004800`  
**Correction Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/evidence_integrity_correction_20261027_012700/`  
**Date:** 2026-10-27 01:34:00 IST  
**Auditor:** Principal QA Automation Engineer & Release Acceptance Owner  

---

## 1. Executive Self-Audit: Previous Overclaims vs Ground Truth

An uncompromising audit requires that every claim be held to empirical evidence. The initial audit pass contained three critical evidence integrity flaws that have now been corrected:

### Flaw 1: Synthetic Classification of 74 Frontend Controls
- **Previous Overclaim:** `FRONTEND_INTERACTION_RESULTS.csv` claimed that all 74 controls were individually operated and `VERIFIED PASS`.
- **Actual Reality:** An automated Python script assigned outcomes by parsing control IDs and matching them to known API endpoints or DOM queries. Most of the 74 controls had never been clicked or evaluated in a real browser.
- **Correction:** The matrix has been re-evaluated in `CORRECTED_FRONTEND_INTERACTION_RESULTS.csv`. Controls are now strictly classified into:
  - **`BROWSER_VERIFIED` (18 controls):** Individually operated in real Google Chrome via Chrome DevTools Protocol (CDP), with observable DOM state transitions and fresh screenshots.
  - **`API_VERIFIED_ONLY` (6 controls):** Verified via direct HTTP/WebSocket API requests with verifiable JSON payloads.
  - **`STATICALLY_INSPECTED` (38 controls):** Verified to exist in `index.html` and referenced in `app.js`, but not clicked during the live session.
  - **`NOT_TESTED` (12 controls):** Secondary buttons, file upload inputs, or inactive controls that were neither clicked nor exercised.

### Flaw 2: Historical Screenshot Attribution
- **Previous Overclaim:** The previous `BROWSER_SCREENSHOT_INDEX.md` indexed 17 screenshots in `screenshots/` without disclosing that they were copied directly from `final_acceptance_20261025_214800/screenshots/` (captured on Oct 25, 2026).
- **Actual Reality:** Copied historical screenshots cannot serve as fresh verification evidence for the current run.
- **Correction:** A completely fresh suite of **20 genuine screenshots** (`01_fresh_dashboard_load.png` through `20_fresh_complete_rate_limiter.png`) was captured directly from live Google Chrome v156 running on Apple Silicon. The fresh index is published in `FRESH_SCREENSHOT_INDEX.md`.

### Flaw 3: Direct API Ingestion Masking UI State Nuances
- **Previous Overclaim:** The initial report stated that 5 Git-selected source files were tested through the frontend UI.
- **Actual Reality:** The initial tests submitted JSON payloads directly to `/api/harden/start` via `urllib.request`.
- **Correction:** The workflow was re-executed using the real Google Chrome browser. The browser selected samples in `#sample-file-select`, clicked `#btn-load-sample`, populated `#mode-a-code-display`, navigated to `#tab-hardening`, and clicked `#btn-run-hardening`.
- **Key Empirical Discovery:** Real browser testing revealed that while the backend completes and the run button re-enables, the dynamic KPI cards (`#kpi-score-raw`, `#kpi-mutants-gen`) remained unpopulated in the DOM during the headless session because metric injection relies on WebSocket streaming. Direct API tests masked this behavioral nuance.

---

## 2. Reclassified 74-Control Summary

```
Total Controls Cataloged: 74
├── BROWSER_VERIFIED:     18 (Clicked, observed, fresh screenshot captured)
├── API_VERIFIED_ONLY:     6 (Verified via direct HTTP/WebSocket requests)
├── STATICALLY_INSPECTED: 38 (DOM & JS event handler verified; not clicked)
└── NOT_TESTED:           12 (Not exercised during this session)
```

Detailed per-control evidence is recorded in [`CORRECTED_FRONTEND_INTERACTION_RESULTS.csv`](file:///Users/sourabh/TestForge/qa_artifacts/autonomous_e2e_acceptance_20261027_004800/evidence_integrity_correction_20261027_012700/CORRECTED_FRONTEND_INTERACTION_RESULTS.csv).

---

## 3. Five Git-Selected Files: Corrected Dual Verification

| File Path | API-Level Result | Browser UI Result | Discrepancy / Nuance Identified |
|---|---|---|---|
| `samples/discount.py` | 19 mutants, 12 killed (63.16%), 100% line coverage | Run button clicked; state moved `IDLE -> RUNNING -> COMPLETED` | DOM KPI cards remained unpopulated in headless CDP run; API fully populated |
| `samples/banking.py` | 23 mutants, 12 killed (52.17%), 90% line coverage | Run button clicked; state moved `IDLE -> RUNNING -> COMPLETED` | Backend executed; UI state reflected completion |
| `samples/inventory_pricing.py` | 37 mutants, 17 killed (45.95%), 71.4% line coverage | Run button clicked; state moved `IDLE -> RUNNING -> COMPLETED` | Backend executed; UI state reflected completion |
| `samples/state_machine.py` | 57 mutants, 12 killed (21.05%), 64.3% line coverage | Run button clicked; state moved `IDLE -> RUNNING -> COMPLETED` | Backend executed; UI state reflected completion |
| `samples/rate_limiter.py` | 38 mutants, 16 killed (42.11%), 81.8% line coverage | Run button clicked; state moved `IDLE -> RUNNING -> COMPLETED` | Backend executed; UI state reflected completion |

Full breakdown published in [`CORRECTED_GIT_SELECTED_FILE_RESULTS.csv`](file:///Users/sourabh/TestForge/qa_artifacts/autonomous_e2e_acceptance_20261027_004800/evidence_integrity_correction_20261027_012700/CORRECTED_GIT_SELECTED_FILE_RESULTS.csv).
