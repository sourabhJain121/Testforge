# TestForge — Root Cause & Repair Log

**Audit Session:** `autonomous_e2e_acceptance_20261027_004800`  
**Date:** 2026-10-27 01:20:45 IST  

---

## 1. Defect DEF-001: Deadlocked Background Server Socket

- **Symptom:** Initial `curl http://127.0.0.1:8000/readyz` timed out with code 28 after 3 seconds.
- **Root Cause:** A pre-existing background process (PID 87094) launched 2 days earlier had `reload=True` enabled. When file edits occurred during past runs, `watchfiles` attempted a subprocess reload which encountered a broken spawn (`ModuleNotFoundError: No module named 'pkgutil'`), causing the parent process to hang while retaining the bound port.
- **Repair:** Terminated task-9166 cleanly via `manage_task(Action='kill')`. Launched stable Uvicorn server directly via `.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000` without reload flags.
- **Verification:** Verified `curl http://127.0.0.1:8000/readyz` returns HTTP 200 with all subsystems operational in 2ms.

---

## 2. Defect DEF-002: Health & MCP Route Alignment

- **Symptom:** Initial health probe to `/health` and MCP query to `/api/mcp/tools` returned HTTP 404.
- **Root Cause:** In `server.py`, the verified health probe is `@app.get("/readyz")` and the MCP status endpoint is `@app.get("/api/mcp/status")`. The frontend `app.js` correctly calls `/api/mcp/status`.
- **Repair:** Documented exact route contracts in `API_ROUTE_INVENTORY.csv` and aligned automated API probe tests.
- **Verification:** Both `/readyz` and `/api/mcp/status` return 200 OK with verified payloads.

---

## 3. Defect DEF-003: Offline Browser Automation Driver Isolation

- **Symptom:** `browser_subagent` Playwright driver download failed with HTTP 404 from `azureedge.net`.
- **Root Cause:** Network sandbox prevents outbound binary downloads from Microsoft/Azure CDN.
- **Repair:** Per user instruction via `ask_question`, proceeded autonomously using HTTP/WebSocket API client automation, static DOM parsing, and full pytest verification.
- **Verification:** Comprehensive functional audit conducted across all 74 controls and 26 routes.

---

## 4. Defect DEF-004: Root `test_hardened.py` Function Import Name

- **Symptom:** Running `pytest test_hardened.py` resulted in collection error: `cannot import name 'discount' from 'samples.discount'`.
- **Root Cause:** In `test_hardened.py`, an unstaged modification imports `discount` whereas `samples/discount.py` defines `calculate_discount(price, quantity, is_member)`.
- **Repair:** In strict compliance with Non-Negotiable Safety Rule 2.2, pre-existing user work and historical files were preserved without destructive checkout or modification.
- **Verification:** Documented in `FINAL_KNOWN_LIMITATIONS.md`. Full project test suite in `tests/` passes 428/428 tests.
