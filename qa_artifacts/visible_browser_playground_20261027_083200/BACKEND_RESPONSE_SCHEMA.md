# TestForge — Backend Response Schema & Field Mapping Audit

**Date:** 2026-10-27 08:34:00 IST  
**Environment:** macOS Apple Silicon, Python 3.13 (`.venv-release`), FastAPI  
**Artifact Directory:** `qa_artifacts/visible_browser_playground_20261027_083200/`  

---

## 1. Authoritative Backend State Schema (`testforge/state.py`)

When `/api/harden/status/{job_id}` returns a job in status `COMPLETED`, `job["final_state"]` contains the serialized Pydantic model `TestForgeState`:

```python
class TestForgeState(BaseModel):
    target_module_path: str = "target.py"
    target_source_code: str = ""
    current_test_code: str = ""
    
    current_iteration: int = 0
    max_iterations: int = 3
    target_mutation_score: float = 85.0
    
    # Statement & Line Coverage
    baseline_line_coverage: float = 0.0
    lines_covered: int = 0
    num_statements: int = 0

    # Baseline Execution Integrity
    baseline_tests_generated: int = 0
    baseline_tests_executed: int = 0
    baseline_passed: bool = False
    baseline_tests_passed: int = 0
    baseline_tests_failed: int = 0

    # Mutation Metrics
    mutants_generated: int = 0
    mutants_executed: int = 0
    mutants_killed: int = 0
    mutants_survived: int = 0
    mutation_execution_errors: int = 0
    final_mutation_score: float = 0.0
    reflection_iterations_performed: int = 0
    final_hardening_status: str = "INITIALIZING"

    mutants: List[MutantRecord] = []
    history: List[IterationMetrics] = []
```

### Iteration Record Schema (`IterationMetrics`):
```python
class IterationMetrics(BaseModel):
    iteration: int
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timed_out_mutants: int
    execution_errors: int = 0
    mutation_score: float = 0.0
    raw_mutation_score: float = 0.0
    adjusted_mutation_score: float = 0.0
    line_coverage_pct: float = 0.0
    duration_seconds: float = 0.0
    baseline_tests_generated: int = 0
    baseline_tests_executed: int = 0
    baseline_passed: int = 0
    baseline_failed: int = 0
    lines_covered: int = 0
```

---

## 2. Identified Frontend Field Mapping Discrepancies (`frontend/app.js`)

A rigorous comparison between `server.py` (`TestForgeState`) and `frontend/app.js` (`renderHardeningResults`) revealed the following exact schema mismatches causing the frontend KPI cards to render blank or default to 0:

| KPI Metric / Component | `frontend/app.js` Expected Path | `server.py` Actual Path | Defect Manifestation |
|---|---|---|---|
| **Mutation Score** | `finalState.mutation_score` | `finalState.final_mutation_score` | Rendered as `0.0%` |
| **Mutants Killed** | `lastIter.mutants_killed` | `finalState.mutants_killed` / `it.killed_mutants` | Rendered as `0` |
| **Mutants Survived** | `lastIter.mutants_survived` | `finalState.mutants_survived` / `it.survived_mutants` | Rendered as `0` |
| **Mutants Generated** | `finalState.mutants.length` | `finalState.mutants_generated` | Rendered as `0` if empty list |
| **Line Coverage %** | `lastIter.line_coverage` / `finalState.baseline_coverage` | `finalState.baseline_line_coverage` / `it.line_coverage_pct` | Rendered as `0.0%` |
| **Baseline Pass Count** | `baseline.tests_passed` (from `finalState.baseline_run`) | `finalState.baseline_tests_passed` | Rendered as `0` |
| **Baseline Fail Count** | `baseline.tests_failed` (from `finalState.baseline_run`) | `finalState.baseline_tests_failed` | Rendered as `0` |
| **Clean Code Verdict** | `baseline.tests_passed > 0` | `finalState.baseline_passed` | Rendered as `⚪ NONE` |
| **Final Hardening Status** | `finalState.hardening_status` | `finalState.final_hardening_status` | Rendered as `'HARDENED'` default |
| **Iteration History Table** | `finalState.iteration_history` | `finalState.history` | Rendered as `'No iteration telemetry recorded.'` |
