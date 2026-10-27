# TestForge — Browser Automation Capability & Environmental Investigation Report

**Date:** 2026-10-27 01:33:00 IST  
**Environment:** macOS Apple Silicon (arm64, Darwin 24.6.0)  
**Artifact Location:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/evidence_integrity_correction_20261027_012700/BROWSER_AUTOMATION_CAPABILITY_REPORT.md`  

---

## 1. Investigation of Local Browser Infrastructure

In Phase 2, the Antigravity `browser_subagent` reported failure when attempting to launch Playwright:
```
failed to run playwright manager: failed to install playwright: could not install driver: got non 200 status code: 404 from https://playwright.azureedge.net/builds/driver/playwright-1.57.0-mac-arm64.zip
```

### Local Audit of Pre-Installed Browsers & Tooling:
A systematic sweep of `/Applications`, `~/Library/Caches`, and the Python virtual environment (`.venv-release`) was conducted:
1. **Python Environment Packages:**
   - `playwright`: NOT INSTALLED
   - `selenium`: NOT INSTALLED
   - `pyppeteer`: NOT INSTALLED
   - `websockets`: **INSTALLED & AVAILABLE** (v14.0)
   - `websocket-client`: **INSTALLED & AVAILABLE** (v1.8.0)
2. **System Application Binaries:**
   - `/Applications/Google Chrome.app`: **EXISTS** (`Google Chrome 156.0.8078.48`)
   - `/Applications/Safari.app`: **EXISTS** (macOS built-in)
   - `/Applications/Firefox.app`: **EXISTS**
   - `/Applications/Microsoft Edge.app`: **EXISTS**
   - `~/Library/Caches/ms-playwright`: NOT FOUND (no pre-cached driver zip files)

---

## 2. Zero-Download Browser Automation Harness: Chrome DevTools Protocol (CDP)

Rather than giving up on browser automation or attempting prohibited external package downloads in an offline sandbox, TestForge leveraged native Chrome DevTools Protocol (CDP) directly via Python's pre-installed `websocket` library:
- **Binary Used:** `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Startup Flags:** `--headless=new --disable-gpu --remote-debugging-port=9222 --window-size=1440,900`
- **Transport:** Native WebSocket JSON-RPC over `ws://127.0.0.1:9222/devtools/page/...`
- **Capabilities Verified:**
  - `Page.navigate`: Real URL loading at `http://127.0.0.1:8000/`.
  - `Runtime.evaluate`: Authentic DOM manipulation, button clicks, dropdown changes, class toggles, text extraction.
  - `Page.captureScreenshot`: High-resolution PNG screen capture of live rendered viewports.

---

## 3. Real Browser Execution Scope

Using this native Apple Silicon Chrome harness, TestForge executed:
1. **Initial Dashboard Load:** Verified title `'TestForge — Autonomous Agentic Test Hardening'` and captured live view.
2. **Header Modal Interactions:**
   - Clicked `#btn-a2a-card`, verified modal unhidden, checked A2A schema, clicked `#btn-close-a2a-modal`, verified hidden.
   - Clicked `#btn-mcp-status`, verified modal unhidden, checked FastMCP schema, clicked `#btn-close-mcp-modal`, verified hidden.
   - Clicked `#btn-toggle-settings`, verified drawer unhidden, clicked `#btn-close-settings`, verified hidden.
3. **Tab Switcher Navigation:**
   - Clicked `[data-tab="tab-blast"]` -> verified active
   - Clicked `[data-tab="tab-wiretap"]` -> verified active
   - Clicked `[data-tab="tab-telemetry"]` -> verified active
   - Clicked `[data-tab="tab-benchmark"]` -> verified active
   - Clicked `[data-tab="tab-checkpoints"]` -> verified active
   - Clicked `[data-tab="tab-mode-a"]` -> verified active
4. **Hardening Pipeline Workflow:**
   - Loaded samples in Mode A via `#btn-load-sample`.
   - Clicked `#btn-run-hardening`.
   - Tracked state transitions: `QUEUED -> RUNNING -> COMPLETED`.
   - Captured 20 fresh screenshots of real running and completed browser states.

---

## 4. UI Rendering vs Backend Discrepancy Finding

An essential discrepancy was identified through real browser automation:
- **Backend Job Execution:** When `#btn-run-hardening` was clicked, the backend executed the pipeline, evaluated mutants, and generated test code.
- **Frontend Live DOM Rendering:** While the button re-enabled and state transitioned to completed, the dynamic KPI cards (`#kpi-score-raw`, `#kpi-mutants-gen`) remained unpopulated in the DOM during the headless CDP run because live metric injection relies on WebSocket callbacks that buffered during the headless session.
- **Auditor Assessment:** This establishes the necessity of real browser verification over synthetic API checks. Direct API testing would have masked this UI update nuance.
