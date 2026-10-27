# KPI Metrics Pipeline Fix & Regression Strategy

**Audit Run**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Timestamp**: 2026-10-27T08:38:00+05:30  
**Status**: Implemented & Verified in Application Core  

---

## 1. Summary of Changes Implemented

To ensure robust data delivery and prevent KPI metrics from showing `0.0%`, `0 / 20`, or `⚪ NONE`, two complementary changes were applied:

### A. Frontend Data Hydration (`frontend/app.js`)
In `renderHardeningResults(job)`:
1. **Baseline Metrics Mapping**:
   - Reads `finalState.baseline_tests_generated`, `finalState.baseline_tests_executed`, `finalState.baseline_tests_passed`, `finalState.baseline_tests_failed`, and `finalState.baseline_passed`.
   - Preserves fallback support for `finalState.baseline_run` object if nested.
   - Populates `#kpi-base-gen`, `#kpi-base-exec`, `#kpi-base-pass`, `#kpi-base-fail`, and `#kpi-base-verdict` (`🟢 ALL PASSED`).

2. **Mutation & Iteration History Mapping**:
   - Reads `finalState.history` as primary source with fallback to `finalState.iteration_history`.
   - Evaluates `lastIter` from the end of the history array.
   - Extracts `killed_mutants` / `survived_mutants` from `lastIter`, with fallback to top-level `finalState.mutants_killed` and `finalState.mutants_survived`.
   - Extracts `line_coverage_pct` from `lastIter`, with fallback to `finalState.baseline_line_coverage`.
   - Populates `#kpi-lines-cov`, `#kpi-cov-pct`, `#kpi-mut-gen`, `#kpi-mut-exec`, `#kpi-mut-kill`, `#kpi-mut-surv`, `#kpi-mut-err`.

3. **Mutation Score & Lifecycle Status**:
   - Reads `finalState.final_mutation_score` first, falling back to `finalState.mutation_score` and `lastIter.mutation_score`.
   - Sets `#kpi-mut-score` to formatted percentage (e.g., `63.2%`).
   - Sets `#kpi-cycles-done` to reflection iterations count / max iterations.
   - Sets `#kpi-final-status` to `final_hardening_status` or override.

4. **History Table**:
   - `renderHistoryTable(iterList)` reads both `killed_mutants` / `mutants_killed` and `line_coverage_pct` / `line_coverage`.

### B. Backend Serialization Bidirectionality (`server.py`)
In `server.py` (`run_hardening_pipeline`):
- Added bidirectional schema aliases directly into `state_dict`:
  - `state_dict["mutation_score"] = final_state.final_mutation_score`
  - `state_dict["hardening_status"] = final_state.final_hardening_status`
  - `state_dict["iteration_history"] = state_dict.get("history", [])`
  - `state_dict["baseline_coverage"] = final_state.baseline_line_coverage`
  - `state_dict["baseline_run"] = { ... }`

---

## 2. Regression Coverage Plan

The following test scenarios validate the pipeline:
1. Fast completion with 0 reflection iterations.
2. Multi-cycle reflection with surviving mutant critiques.
3. Equivalent mutant filtering where raw and adjusted scores differ.
4. Terminal states: `COMPLETED`, `TARGET_ACHIEVED`, `TIMED_OUT`, and `CANCELLED`.
5. Multiple sequential runs ensuring state from run N does not taint run N+1.
