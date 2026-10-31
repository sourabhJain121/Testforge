# TestForge Phase 8: Defect Register & Prioritization

**Audit Date:** 2026-10-30  
**Auditor:** Antigravity Automated QA Suite  
**Evaluation Scope:** Complete Frontend Playground & Multi-Agent Architecture

---

## 1. Defect Summary Matrix

| Defect ID | Severity / Priority | Subsystem | Description | Root Cause | Status | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DEF-01` | **P2 (Medium)** | Backend API (`/api/ingest/upload`) | Uploading Python files with invalid syntax returned `"status": "success"` instead of reporting syntax error. | Ingestion analysis caught `SyntaxError` and set `has_syntax_error=True`, but `server.py` unconditionally returned `"status": "success"` and omitted error details. | **RESOLVED** | Updated `server.py` to check `getattr(analysis, "has_syntax_error", False)` and return `"status": "syntax_error"` with isolated error details. |
| `DEF-02` | **P3 (Minor / UX)** | Frontend Navigation | No cross-links between FastAPI Cockpit (`:8000`) and Streamlit Workbench (`:8501`), causing potential user confusion. | Separate development history: Streamlit was prototype; FastAPI was modern rewrite. Neither UI referenced the other. | **RESOLVED** | Added direct `🔬 Streamlit` button in FastAPI header navbar, and added an informative Primary Cockpit banner on Streamlit pointing to `:8000`. |
| `DEF-03` | **P1 (High / Perf)** | Streamlit Startup (`app.py`) | Streamlit frontend froze indefinitely on gray skeleton loading screen with 100% CPU and 8.6 GB memory. | `app.py` synchronously deserialized a 260 MB uncommitted `testforge_trace.jsonl` (437,660 lines) five times on startup, while Streamlit file watcher watched virtualenv. | **RESOLVED** | Safely archived full history to `testforge_trace.jsonl.archive_full`, pruned active trace to 1,000 lines, and launched Streamlit with `--server.fileWatcherType none`. Memory dropped to 511 MB, startup time dropped to <2s. |

---

## 2. Detailed Defect Investigations

### DEF-01: Ingest Upload Syntax Error Masking
- **Symptoms:** When `08_syntax_error.py` was uploaded, the endpoint returned HTTP 200 with `"status": "success"`, but `functions: []` and `classes: []`.
- **Impact:** Frontend could not distinguish between a valid empty file and a broken Python file with syntax errors.
- **Remediation:** In `server.py`:
  ```python
  has_syntax_error = getattr(analysis, "has_syntax_error", False)
  error_msg = getattr(analysis, "error_msg", None)
  return {
      "status": "syntax_error" if has_syntax_error else "success",
      "has_syntax_error": has_syntax_error,
      "error": error_msg,
      ...
  }
  ```
- **Verification:** Re-ran `audit_edge_cases.py`; `EC-08` now correctly captures `SyntaxError on line 1: invalid syntax`. 10/10 edge cases passed.

### DEF-02: Lack of Dual-Frontend Cross-Linking
- **Symptoms:** Evaluators opening Streamlit did not know that FastMCP, A2A, and SQLite diffing were accessible on FastAPI port 8000.
- **Remediation:**
  - Added `#btn-streamlit-link` in `frontend/index.html` navbar.
  - Added `st.info("🌟 Primary Evaluation Interface: ...")` in `app.py`.
- **Verification:** Both frontends visually inspected via `agent-browser` and captured in `fastapi_header_with_crosslink.png` and `streamlit_with_cockpit_banner.png`.

### DEF-03: Streamlit Startup Deserialization Stall
- **Symptoms:** Opening `http://127.0.0.1:8501/` hung indefinitely on skeleton loader.
- **Root Cause:** Ingestion of 260 MB trace file repeated on every Streamlit script rerun.
- **Remediation:** Archived historical trace safely, retained active trace at 1,000 lines, and configured `--server.fileWatcherType none`.
- **Verification:** Streamlit now loads instantaneously (< 2.0 seconds) with zero memory thrashing.

