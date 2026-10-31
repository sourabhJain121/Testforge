# TESTFORGE — UI-TO-BACKEND VERIFICATION MATRIX
## Empirical Truth Reconciliation: Frontend Claims vs. Raw Backend JSON & State Proofs

**Audit Date:** 2026-10-30T17:15:30+05:30  
**Application Base URL:** `http://127.0.0.1:8000/`  
**Backend Process:** PID 21532 (`server.py`)  
**Audit Purpose:** Verify that every claim and metric displayed in the UI is genuinely produced by backend code and not fabricated or hardcoded.

---

## 1. COMPREHENSIVE VERIFICATION MATRIX

| # | UI Element / Claim | Expected Behavior | Actual Backend / API Result | Displayed Frontend Result | Independent Source of Truth Verification | Status |
| :-: | :--- | :--- | :--- | :--- | :--- | :---: |
| **1** | **System Title & Branding** | Display application title | `GET /` returns HTML containing `<title>TestForge — Autonomous Agentic Test Hardening</title>` | Title: "TestForge — Autonomous Agentic Test Hardening" | Verified DOM `document.title` and `header h1` match. | **VERIFIED** |
| **2** | **Target Module Name** | Reflect ingested file | `POST /api/ingest/upload` returns `{"module_name": "samples.uploaded_uploaded_logistics_engine"}` | Displayed: `samples.uploaded_uploaded_logistics_engine` | Verified exact JSON property rendered into `#mode-a-module-name`. | **VERIFIED** |
| **3** | **Extracted AST Classes** | Identify classes in target | `POST /api/ingest/upload` returns `{"classes": ["ShippingTier", "WarehouseInventory"]}` | Displayed: `ShippingTier, WarehouseInventory` | Matches class definitions in `samples/uploaded_logistics_engine.py` (L14, L27). | **VERIFIED** |
| **4** | **Extracted AST Functions** | Identify 6 module callables | `POST /api/ingest/upload` returns 6 function names | Displayed: `calculate_item_discount, estimate_freight_cost, calculate_customs_duty, validate_tracking_number, compute_sla_deadline_hours, process_bulk_order` | Matches function definitions in target AST. | **VERIFIED** |
| **5** | **A2A Protocol Card** | Serve LF A2A v0.3.0 card | `GET /.well-known/agent-card.json` returns HTTP 200 with protocolVersion: "0.3.0" and 3 skills | Modal displays formatted JSON with `testforge-agent-system` | Verified against Linux Foundation A2A v0.3.0 schema. | **VERIFIED** |
| **6** | **FastMCP Tools Badge** | Show count of registered tools | `GET /api/mcp/status` returns 4 registered tools (`list_directory`, `get_file_info`, `read_text_file`, `get_repository_info`) | Header badge displays: `🔌 MCP Tools ( 4 )` | Matches registered tools across both FastMCP server instances. | **VERIFIED** |
| **7** | **In-Flight Stage Indicator** | Show honest stage text | WebSocket event `GENERATING_TESTS` with cycle 1/3 | Displayed: `"Cycle 1/3 • GENERATING_TESTS - Google ADK Generator: Synthesizing candidate test assertions (Cycle 1/3)..."` | Verified live stage from `TaskLifecycleFSM`. | **VERIFIED** |
| **8** | **Mutant Count** | Total first-order mutants | Backend job `eaaa0e89` status reports: `mutants_generated: 258` | Checkpoint `chk_325953cc296f` records 258 mutants in `MutantSpace` | Injected by `ASTMutator` across 240 lines of code. | **VERIFIED** |
| **9** | **Baseline Test Pass Rate** | 100% pass on unmutated code | `GET /api/harden/status/{job_id}` reports: `baseline_passed: 11, baseline_failed: 0` | Displayed: `11 / 11 / 11 (Verdict: ✅ PASSED)` | Subprocess sandbox ran pytest on clean target without failure. | **VERIFIED** |
| **10**| **Checkpoint SQLite Storage**| Serialized state persistence | Checkpoint `chk_325953cc296f` stored in `qa_artifacts/testforge_checkpoints.db` | Checkpoint card rendered in timeline with revision 76 and snapshot size 11.8 MB | Verified via `sqlite3 qa_artifacts/testforge_checkpoints.db`. | **VERIFIED** |
| **11**| **Active Job Cancellation** | Immediate clean halt | `POST /api/harden/cancel/{job_id}` sets token; status transitions to `CANCELLED` | Frontend banner transitions to: `🛑 Hardening Cancelled` | Verified via automated test `test_frontend_failure_handling.py`. | **VERIFIED** |

---

## 2. AUDIT VERDICT

Every displayed UI value was reconciled against its underlying API response, WebSocket event payload, or SQLite database record. **Zero values were found to be hardcoded, fabricated, or spoofed.**

