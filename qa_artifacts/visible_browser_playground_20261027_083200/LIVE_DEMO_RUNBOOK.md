# Live Visible Browser Playground Runbook

**Environment**: Headed Google Chrome (v156.0.8078.48) on macOS Apple Silicon  
**Backend Port**: `http://127.0.0.1:8000/`  
**Chrome Remote Debugging**: `http://127.0.0.1:9222/`  
**Execution Mode**: Visible GUI, headed mode, window brought to foreground via `osascript`  
**Date**: 2026-10-27  
**Artifact Directory**: `qa_artifacts/visible_browser_playground_20261027_083200/`  

---

## 1. How the Visible Browser Was Launched & Controlled

1. **Persistent Headed Chrome Launch**:
   Google Chrome was started directly with a dedicated user data profile:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --remote-debugging-port=9222 \
     --user-data-dir="/tmp/chrome_testforge_debug" \
     "http://127.0.0.1:8000/"
   ```
2. **Foreground Activation**:
   Before and during each workflow stage, Chrome was brought to the front of the display:
   ```bash
   osascript -e 'tell application "Google Chrome" to activate'
   ```
3. **Real DevTools Protocol Automation**:
   The test orchestrator connected to the headed Chrome instance via `ws://127.0.0.1:9222/devtools/page/...`. All interactions (tab switching, select option choice, button click events, DOM reads, and PNG screenshots) were dispatched directly to the active visible page.

---

## 2. Sequence of Executed Live Workflows

| Step | Target File | Action | Observed Result | Screenshot |
| :--- | :--- | :--- | :--- | :--- |
| **00** | Dashboard | Initial Page Load | Dashboard rendered with active status pills and hero banner | `00_baseline_dashboard.png` |
| **01** | `samples/discount.py` | Load Sample & Run Hardening | Ingested 545 chars, ran 3 iterations. Score: **63.2%**, 12 killed / 7 survived. Baseline: 1 passed. | `01_discount_hardening_complete.png` |
| **02** | `samples/banking.py` | Load Sample & Run Hardening | Ingested 549 chars, ran 3 iterations. Score: **52.2%**, 12 killed / 11 survived. Baseline: 1 passed. | `02_banking_hardening_complete.png` |
| **03** | `samples/inventory_pricing.py` | Load Sample & Run Hardening | Ingested 1579 chars, ran 3 iterations. Score: **46.0%**, 17 killed / 20 survived. Baseline: 1 passed. | `03_inventory_pricing_hardening_complete.png` |
| **04** | `samples/state_machine.py` | Load Sample & Run Hardening | Ingested 1399 chars, ran 3 iterations. Score: **21.1%**, 12 killed / 45 survived. Baseline: 1 passed. | `04_state_machine_hardening_complete.png` |
| **05** | `samples/rate_limiter.py` | Load Sample & Run Hardening | Ingested 1214 chars, ran 3 iterations. Score: **42.1%**, 16 killed / 22 survived. Baseline: 1 passed. | `05_rate_limiter_hardening_complete.png` |
| **06** | Cancellation | Start run & click `#btn-cancel-hardening` | Pipeline cooperatively cancelled; UI rendered `🛑 Hardening Cancelled` | `06_cancellation_state.png` |
| **07** | Empty Guard | Attempt run without loaded source | Guard prevented execution, displayed warning toast | N/A (Guarded) |
| **08** | Secondary Controls | Toggled A2A, MCP, Settings, Wiretap, Telemetry, Checkpoints, Benchmark | All modals opened/closed cleanly; tabs hydrated without console crashes | `07_a2a_drawer.png` to `13_checkpoints_view.png` |
| **09** | Final View | Retained final completed hardening view on screen | TestForge application remains open on screen for human verification | `14_final_completed_hardening_demonstration.png` |

---

## 3. How to Repeat the Live Demo

To repeat the demonstration manually or via automation:
1. Ensure the backend is active:
   ```bash
   .venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
   ```
2. Open Google Chrome in headed debugging mode:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 "http://127.0.0.1:8000/"
   ```
3. Run the live verification runner:
   ```bash
   .venv-release/bin/python qa_artifacts/visible_browser_playground_20261027_083200/run_live_visible_playground.py
   ```
4. Watch Google Chrome execute the workflows live on your monitor.
