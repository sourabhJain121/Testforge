# Root Cause & Fix Log: Autonomous Repair

**Audit Directory:** `qa_artifacts/autonomous_repair_20261027_112700/`  
**Repository:** `/Users/sourabh/TestForge`

---

## 1. Issue TF-DEF-006: Trailing Whitespace & Blank Line at EOF

- **Symptoms:** `git diff --check` failed with exit code 2.
- **Root Cause:** Manual formatting edits in previous audit added spaces on blank lines and a double newline at end of file.
- **Fix:**
  - In `frontend/app.js`: Cleared trailing spaces in template literal lines 2237, 2250, 2254, 2255.
  - In `tests/test_mutation_scores.py`: Removed line 190.
- **Verification:** `git diff --check` exits with status `0` cleanly.

---

## 2. Issue TF-DEF-007: FastAPI on_event Deprecation Warning

- **Symptoms:** Pytest and server startup emitted:
  ```text
  server.py:70: DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.
  ```
- **Root Cause:** FastAPI deprecated `@app.on_event("startup")` in modern Starlette/FastAPI versions in favor of `lifespan`.
- **Fix:**
  In `server.py`:
  ```python
  from contextlib import asynccontextmanager

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      try:
          loop = asyncio.get_running_loop()
          global_websocket_hub.set_event_loop(loop)
          global_websocket_hub.attach_to_registry()
          logger.info("WebSocket event hub initialized on server startup.")
      except Exception as exc:
          logger.warning(f"Error during WebSocket hub startup hook: {exc}")
      yield

  app = FastAPI(..., lifespan=lifespan)
  ```
- **Verification:** Ran `pytest tests/test_teacher_review_improvements.py`. Deprecation warning count dropped from 4 to 2; `server.py` warning is completely eliminated.

---

## 3. Issue TF-DEF-008: Upstream CrewAI Deprecation Warnings

- **Symptoms:** Pytest emitted warnings:
  ```text
  DeprecationWarning: function_calling_llm is deprecated and will be removed in a future release.
  DeprecationWarning: allow_code_execution is deprecated and will be removed in v2.0.
  ```
- **Investigation:** Grepped entire codebase for `function_calling_llm` and `allow_code_execution`. Neither argument is passed by TestForge code. TestForge creates `Agent` using:
  ```python
  Agent(role=..., goal=..., backstory=..., llm=self.llm_bridge, verbose=self.verbose, allow_delegation=False)
  ```
- **Root Cause:** CrewAI v0.100.x internal codebase contains `@property` definitions for `function_calling_llm` and `allow_code_execution` marked `@deprecated`. CrewAI's own internal initialization methods in `crewai/agent/core.py:425` and `crewai/crew.py:650` read `self.function_calling_llm` unconditionally, triggering their own deprecation warnings.
- **Handling Policy:** In accordance with Part 4.3, third-party warnings are documented with their trigger and upstream cause; they are not globally silenced with suppressors or hidden.

---

## 4. Issue TF-DEF-009: Honest Mutation Target Presentation

- **Symptoms:** Jobs failing to achieve 85% target were previously labeled `COMPLETED` without clear distinction of whether the target mutation score was met.
- **Root Cause:** Finite reflection budget (`max_iterations = 3`) halted execution when surviving mutants were semantic invariants or when candidate tests were quarantined by the clean code validator.
- **Fix:** Enhanced `#hardening-verdict-banner` and KPI cards in `frontend/app.js` with tripartite status badges:
  - Baseline: `100% Passed`
  - Pipeline: `Finished`
  - Target: `Unreached (63.2% vs 85.0%)`
  Added dynamic explanation explaining boundary conditions and equivalent mutants.
- **Verification:** In-browser headless and headed runs confirm exact UI-to-backend parity.
