# Defect Repair Log

**Audit Directory**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Date**: 2026-10-27  

---

## Repaired Defect: TF-DEF-005 — KPI Metric Cards Blank / 0.0% Display

### 1. Symptom & Evidence
- Backend logged successful completion with mutation scores (e.g. `63.16%`, `12 killed`, `7 survived`).
- However, during browser automation runs, `#kpi-mut-score` displayed `0.0%`, `#kpi-mut-kill` displayed `0`, and `#kpi-base-verdict` displayed `⚪ NONE`.

### 2. Root Cause Analysis
In `frontend/app.js` (`renderHardeningResults`), the JavaScript controller looked for:
- `finalState.mutation_score` (actual `TestForgeState` property: `final_mutation_score`)
- `finalState.iteration_history` (actual `TestForgeState` property: `history`)
- `lastIter.mutants_killed` (actual `IterationMetrics` property: `killed_mutants`)
- `lastIter.mutants_survived` (actual `IterationMetrics` property: `survived_mutants`)
- `lastIter.line_coverage` (actual `IterationMetrics` property: `line_coverage_pct`)
- `finalState.baseline_run.tests_passed` (actual `TestForgeState` properties: `baseline_tests_passed`, `baseline_passed`)
- `finalState.hardening_status` (actual `TestForgeState` property: `final_hardening_status`)

Because property lookups returned `undefined`, safe navigation fallbacks (`|| 0`, `|| 'HARDENED'`) populated the cards with default zeroed text without throwing unhandled exceptions.

### 3. Applied Repair
1. **Frontend (`frontend/app.js`)**:
   Updated `renderHardeningResults` and `renderHistoryTable` to support both canonical and alias names using null-coalescing operators:
   ```javascript
   const finalScore = finalState.final_mutation_score != null
     ? finalState.final_mutation_score
     : (finalState.mutation_score != null
       ? finalState.mutation_score
       : (lastIter ? (lastIter.mutation_score || lastIter.raw_mutation_score || 0) : 0));
   dom.kpiMutScore.textContent = `${finalScore.toFixed(1)}%`;
   ```
2. **Backend (`server.py`)**:
   Updated `job_record["final_state"] = state_dict` to include bidirectional alias keys:
   ```python
   state_dict["mutation_score"] = getattr(final_state, "final_mutation_score", 0.0)
   state_dict["hardening_status"] = getattr(final_state, "final_hardening_status", "UNKNOWN")
   state_dict["iteration_history"] = state_dict.get("history", [])
   state_dict["baseline_coverage"] = getattr(final_state, "baseline_line_coverage", 0.0)
   state_dict["baseline_run"] = { ... }
   ```

### 4. Verification Evidence
All 5 sample source files tested through the visible Google Chrome browser verified `100% MATCH` between rendered DOM elements and the backend responses:
- `discount.py`: `63.2%` (12 killed / 19 generated) -> **MATCH**
- `banking.py`: `52.2%` (12 killed / 23 generated) -> **MATCH**
- `inventory_pricing.py`: `46.0%` (17 killed / 37 generated) -> **MATCH**
- `state_machine.py`: `21.1%` (12 killed / 57 generated) -> **MATCH**
- `rate_limiter.py`: `42.1%` (16 killed / 38 generated) -> **MATCH**
