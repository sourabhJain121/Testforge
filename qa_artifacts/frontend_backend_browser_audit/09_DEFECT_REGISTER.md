# 09 — Defect Register & Anomaly Tracking

**TestForge Master Frontend, Backend & Browser Acceptance Audit**  
**Audit Policy:** Strict Audit-Only Mode — Application Code Freeze Enforced (No Code Modifications Performed)  
**Classification Scheme:** Critical, High, Medium, Low, Informational / Design

---

## 1. Defect Summary Table

| Defect ID | Severity | Component | Summary | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | Low / Design | Backend Orchestrator | Hardening loop writes candidate tests to root `test_hardened.py` | Open (Freeze Active) |
| **DEF-02** | Medium / Automation | Streamlit Tornado Server | Rapid consecutive headless browser re-opens cause CLOSE_WAIT socket hang | Open (Freeze Active) |
| **DEF-03** | Low / Cosmetic | Frontend Code Editor | Benign Monaco/Ace Web Worker fallback warning logged to console | Open (Freeze Active) |
| **DEF-04** | Low / Accessibility | Streamlit Sliders | Double label voiced in accessibility tree (`Max Reflection Iterations ...`) | Open (Upstream) |

---

## 2. Detailed Defect Dossiers

### DEF-01: Candidate Test Output Overwrites Working Tree File (`test_hardened.py`)
- **Severity:** Low (Design Behavior)
- **Component:** `testforge/orchestrator.py` & `testforge/state.py`
- **Reproduction Steps:**
  1. Open FastAPI Dashboard at `http://127.0.0.1:8000/`.
  2. Ingest `discount.py` as active target.
  3. Switch to Hardening Lab and click `⚡ Run Hardening Pipeline`.
  4. Observe `test_hardened.py` in repository root.
- **Observed Behavior:**
  The baseline test generation agent writes the nominal candidate test suite (`def test_calculate_discount_nominal(): assert calculate_discount() is not None`) directly into `/Users/sourabh/TestForge/test_hardened.py`.
- **Root Cause:**
  The default output path for synthesized test code in `TestForgeOrchestrator` points to `Path("test_hardened.py")`.
- **Impact:**
  Alters the uncommitted working tree file `test_hardened.py`. (Recorded under Modified Files).
- **Recommended Post-Freeze Action:**
  Parameterize the output path to write candidate test suites to an isolated run artifact folder (e.g., `artifacts/runs/{job_id}/test_hardened.py`) or return candidate code purely in-memory through the REST API, keeping the repository root test clean.

---

### DEF-02: Streamlit Tornado WebSocket Socket Retention on Rapid Headless Re-Opens
- **Severity:** Medium (Automation / Test Harness Edge Case)
- **Component:** Streamlit Server / Tornado WebSocket Handler
- **Reproduction Steps:**
  1. Launch Streamlit via `streamlit run app.py`.
  2. Run a browser automation script that calls `agent-browser open http://127.0.0.1:8501` multiple times in rapid succession (< 1s interval) without calling `agent-browser close`.
  3. The TCP connection enters `CLOSE_WAIT` and causes subsequent `open` commands to time out after 30 seconds.
- **Workaround Verified During Audit:**
  Invoking `agent-browser close --all` before executing distinct browser automation suites cleanly flushes all active browser contexts and allows immediate reconnects.
- **Recommended Post-Freeze Action:**
  Ensure browser test runners implement explicit session lifecycle hooks (`close()` after each test suite) and configure `--server.headless true` with appropriate timeout parameters.

---

### DEF-03: Benign Web Worker Console Warning in Code Editor
- **Severity:** Low (Cosmetic Warning)
- **Component:** `frontend/index.html` & `frontend/app.js`
- **Reproduction Steps:**
  1. Open Web Dashboard in browser.
  2. Open Developer Tools Console.
  3. Observe warning: `[warning] No script tag of type "javascript/worker" was found and "useWorker" is true. Not using web worker.`
- **Root Cause:**
  The embedded syntax highlighter defaults to web worker thread processing, but no separate worker script file is registered in the static assets. It falls back seamlessly to main-thread parsing.
- **Recommended Post-Freeze Action:**
  Configure `editor.setOption("useWorker", false);` in `app.js` or include the static worker script file.

---

### DEF-04: Streamlit Slider Label Duplication in Accessibility Tree
- **Severity:** Low (Screen-Reader Accessibility)
- **Component:** Streamlit Native UI Widgets
- **Reproduction Steps:**
  1. Open Streamlit at `http://127.0.0.1:8501`.
  2. Inspect accessibility snapshot via `agent-browser snapshot -i`.
  3. Notice `slider "Max Reflection Iterations Max Reflection Iterations"`.
- **Root Cause:**
  Streamlit renders both a visual `<label>` tag and an `aria-label` attribute on the slider element.
- **Recommended Post-Freeze Action:**
  Upstream Streamlit library behavior; no local code change required.

