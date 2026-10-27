# KPI Defect Reproduction and Root-Cause Analysis

**Timestamp**: 2026-10-27T08:36:00+05:30  
**Audit Directory**: `qa_artifacts/visible_browser_playground_20261027_083200/`  
**Target Environment**: Headed Google Chrome (v156.0.8078.48) on macOS Apple Silicon  
**Backend**: FastAPI / Uvicorn listening on `http://127.0.0.1:8000/`  

---

## 1. Problem Statement & Historical Hypothesis

In previous headless CDP audits, an anomaly was noted:
- The backend completed hardening runs successfully, reaching `TaskLifecycleState.COMPLETED`.
- Backend logs and responses contained verified mutation metrics (e.g., 63.16% score, 12 mutants killed, 7 survived).
- However, the headless CDP audit reported that DOM KPI cards remained unpopulated (`0.0%`, `0 / 20`, `⚪ NONE`).
- The previous audit hypothesized WebSocket message buffering or race conditions during event subscription as the potential root cause.

---

## 2. Definitive Root Cause Discovered

Upon static and dynamic trace analysis between `testforge/state.py`, `server.py`, and `frontend/app.js`, the defect was **conclusively diagnosed as a field name / schema mismatch** in `frontend/app.js`'s `renderHardeningResults(job)`:

### Trace of Data Flow:
```
Backend TestForgeState (testforge/state.py)
   │
   ├── final_mutation_score (float, e.g. 63.1578)
   ├── final_hardening_status (str, "TARGET_ACHIEVED" / "TIMEOUT_TERMINATED")
   ├── baseline_line_coverage (float, e.g. 100.0)
   ├── baseline_tests_passed (int, e.g. 3)
   ├── baseline_tests_failed (int, e.g. 0)
   ├── baseline_passed (bool, True)
   ├── mutants_killed (int, e.g. 12)
   ├── mutants_survived (int, e.g. 7)
   ├── mutants_generated (int, e.g. 19)
   └── history (List[IterationMetrics])
          ├── killed_mutants
          ├── survived_mutants
          ├── line_coverage_pct
          └── mutation_score
   │
   ▼
server.py Serialization (/api/harden/status/{job_id})
   job["final_state"] = state_dict  # (Exact dump of TestForgeState)
   │
   ▼
Frontend Event / Polling Handler (frontend/app.js)
   renderHardeningResults(job)
   │
   ├── Checks finalState.mutation_score       ──❌ (Backend field is final_mutation_score) -> defaults to 0.0%
   ├── Checks finalState.iteration_history    ──❌ (Backend field is history) -> undefined
   ├── Checks lastIter.mutants_killed         ──❌ (IterationMetrics field is killed_mutants) -> undefined -> 0
   ├── Checks lastIter.mutants_survived       ──❌ (IterationMetrics field is survived_mutants) -> undefined -> 0
   ├── Checks finalState.baseline_run         ──❌ (Backend fields are flat: baseline_tests_passed, etc.) -> undefined -> 0, "NONE"
   ├── Checks finalState.hardening_status     ──❌ (Backend field is final_hardening_status) -> fallback 'HARDENED'
   └── Calls renderHistoryTable(finalState.iteration_history || []) ──❌ -> renders "No iteration telemetry recorded."
```

### Table of Discrepancies:

| Metric | Frontend Expected Path (`app.js`) | Backend Authoritative Path (`TestForgeState`) | Consequence When Mismatched |
| :--- | :--- | :--- | :--- |
| **Mutation Score** | `finalState.mutation_score` | `finalState.final_mutation_score` | KPI card `#kpi-mut-score` displays `0.0%` |
| **Mutants Killed** | `lastIter.mutants_killed` | `lastIter.killed_mutants` or `finalState.mutants_killed` | KPI card `#kpi-mut-kill` displays `0` |
| **Mutants Survived** | `lastIter.mutants_survived` | `lastIter.survived_mutants` or `finalState.mutants_survived` | KPI card `#kpi-mut-surv` displays `0` |
| **Line Coverage** | `lastIter.line_coverage` or `finalState.baseline_coverage` | `lastIter.line_coverage_pct` or `finalState.baseline_line_coverage` | KPI card `#kpi-cov-pct` displays `0.0%` |
| **Baseline Tests Passed** | `finalState.baseline_run.tests_passed` | `finalState.baseline_tests_passed` | KPI card `#kpi-base-pass` displays `0` |
| **Baseline Tests Failed** | `finalState.baseline_run.tests_failed` | `finalState.baseline_tests_failed` | KPI card `#kpi-base-fail` displays `0` |
| **Baseline Verdict** | `finalState.baseline_run.tests_failed === 0` | `finalState.baseline_passed` | KPI card `#kpi-base-verdict` displays `⚪ NONE` |
| **Hardening Status** | `finalState.hardening_status` | `finalState.final_hardening_status` | Verdict banner misses exact terminal reason |
| **Iteration History** | `finalState.iteration_history` | `finalState.history` | History table displays empty telemetry state |

---

## 3. Secondary Factor: Element Selector Mismatch in Historical Auditing Script

The earlier headless audit script asserted presence of `#kpi-score-raw` and `#kpi-mutants-gen`. In reality, `frontend/index.html` defines the IDs as:
- `#kpi-mut-score`
- `#kpi-mut-gen`
- `#kpi-mut-kill`
- `#kpi-mut-surv`

Therefore, part of the historical "blank cards" diagnosis was also an artifact of invalid element queries in the automated test runner, layered on top of the JavaScript schema mismatch.

---

## 4. Verification & Reproduction Conclusion

The root cause is 100% deterministic and reproducible:
1. When `renderHardeningResults(job)` runs on a completed job, JavaScript attempts property lookups that evaluate to `undefined`.
2. Safe navigation fallbacks (`|| 0`, `|| 'HARDENED'`) catch the `undefined` values and populate the DOM with zeroed metrics rather than raising an uncaught exception.
3. This creates the illusion that the UI failed to receive data, when in reality the data was delivered completely but ignored due to key naming mismatches.

The remediation requires a synchronized dual-layer fix:
1. Update `frontend/app.js` to support both canonical schema variants with null-coalescing (`final_mutation_score ?? mutation_score`).
2. Update `server.py` job serialization to provide bidirectional alias keys on the `final_state` object.
