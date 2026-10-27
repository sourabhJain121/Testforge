# Issue Register: Autonomous Repair & Teacher-Review Readiness

**Audit Directory:** `qa_artifacts/autonomous_repair_20261027_112700/`  
**Repository:** `/Users/sourabh/TestForge`

---

## Issue Catalog

| Issue ID | Severity | Component | Summary | Status | Resolution |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **TF-DEF-006** | LOW | `frontend/app.js`, `tests/test_mutation_scores.py` | Trailing whitespace and extra newline at EOF caused `git diff --check` to exit code 2. | **RESOLVED** | Removed trailing whitespace in `app.js:2237-2256` and trimmed newline at EOF of `test_mutation_scores.py`. |
| **TF-DEF-007** | MEDIUM | `server.py` | `@app.on_event("startup")` emits project-owned `DeprecationWarning` under FastAPI. | **RESOLVED** | Refactored to standard `asynccontextmanager lifespan(app: FastAPI)` and passed to `FastAPI(lifespan=lifespan)`. |
| **TF-DEF-008** | LOW | Upstream `crewai` | CrewAI v0.100+ emits deprecation warnings on `function_calling_llm` and `allow_code_execution`. | **DOCUMENTED** | Verified TestForge passes neither argument; warnings originate inside CrewAI's own property checks. Documented upstream remediation path without suppressing warnings. |
| **TF-DEF-009** | MEDIUM | `frontend/app.js`, `server.py` | UI formerly showed unearned success or ambiguous status when mutation target score was unreached. | **RESOLVED** | Implemented honest tripartite status badges (`Baseline: 100% Passed`, `Pipeline: Finished`, `Target: Unreached`), exposed target alongside actual score, and detailed surviving mutant boundary reasons. |
| **TF-DEF-010** | MEDIUM | `frontend/index.html`, `server.py` | Lack of in-browser execution verification for FastMCP and Agent2Agent protocols. | **RESOLVED** | Added safe diagnostic test runners inside `#mcp-modal` and `#a2a-modal` backed by secure endpoints `/api/mcp/test` and `/api/a2a/test`. |
| **TF-DEF-011** | MEDIUM | `frontend/app.js` | Progress bar relied on simulated increment `progressSim += 12`. | **RESOLVED** | Replaced with real FSM lifecycle state polling (`job.lifecycle_state`) and dynamic 5-partition Blackboard strip. |
