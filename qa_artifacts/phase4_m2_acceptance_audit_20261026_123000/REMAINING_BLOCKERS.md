# Remaining Blockers and Pre-Evaluation Action Items

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Pre-Evaluation Acceptance Audit  
**Timestamp:** `20261026_123000`  

---

## 1. Classification of Findings

| Severity | ID | Title | Component | Impact | Status |
|---|---|---|---|---|:---:|
| **BLOCKER** | — | *None* | — | No blocker prevents repository operation or milestone acceptance. | **N/A** |
| **HIGH** | **H-01** | Benchmark Runner Denominator / False Positive Disconnect | `testforge/corpus/runner.py` | Benchmark reports overstate mutation score on suites containing broken tests. | **OPEN (Follow-up)** |
| **MEDIUM** | **M-02** | Shared Module Context in Granular Isolation | `testforge/sandbox.py` | Tests depending on external fixtures or shared globals may fail in isolated sandboxes. | **PLANNED (Milestone 4.1.3)** |
| **LOW** | **L-01** | Pytest stdout Regex Parsing Dependency | `testforge/sandbox.py` | Relies on standard pytest `-v` output string formatting. | **ACCEPTED RISK** |
| **LOW** | **L-02** | Ephemeral Root File Modification Side-Effects | `server.py`, `tests/` | Running tests updates root `test_hardened.py` and `benchmark_results.json`. | **MAINTENANCE ITEM** |

---

## 2. In-Depth Remediation Plans

### Finding H-01 (HIGH) — Benchmark Runner Denominator / False Positive Disconnect
- **Description:** In `testforge/corpus/runner.py:599`, `runner.evaluate_mutants_parallel(test_code_to_eval, mutants)` evaluates candidate tests against all AST mutants without first filtering out candidate tests that fail on clean reference code (`tests_failed_on_reference > 0`). Because `evaluate_mutants_parallel` defaults to `baseline_passed: bool = True`, any test failure during execution against a mutant is interpreted as a mutant kill, even if the failure was caused by a pre-existing hallucinated assertion.
- **Why it does not block Phase 4.1.2 acceptance:**
  The production orchestrator (`orchestrator.py`) already implements the correct behavior via `GranularTestValidator.validate_and_filter_candidate_suite`, which isolates, validates against clean code, and quarantines broken candidate tests. The defect is confined to the offline benchmark runner harness (`testforge/corpus/runner.py`).
- **Remediation for Pre-Teacher Evaluation:**
  1. In `testforge/corpus/runner.py:599`, filter `test_code_to_eval` using `ParallelSandboxRunner.validate_and_filter_candidate_suite` before mutant evaluation.
  2. Pass `baseline_passed = (failed_ref == 0)` to `evaluate_mutants_parallel`.
  3. Re-run the benchmark across the 5 fixtures with filtered suites and update the comparative report.

---

### Finding M-02 (MEDIUM) — Shared Module Context in Granular Isolation
- **Description:** `GranularTestValidator` splits test modules into the preamble (imports and helper functions) and individual test functions. If candidate tests rely on module-level mutable globals, class-level setup (`setup_class`), or pytest fixtures defined outside the preamble (e.g. in external `conftest.py` files), running them in isolation will raise `NameError` or `FixtureLookupError`.
- **Planned Milestone 4.1.3 Resolution:**
  1. Enhance AST extraction to identify module-level assignments and fixture definitions.
  2. Inject captured shared setup definitions into individual test execution sandboxes alongside the preamble.
  3. Support grouped execution for parametrized suites and test classes.

---

### Finding L-02 (LOW) — Ephemeral Root File Modification Side-Effects
- **Description:** Running `tests/test_fast_benchmarking.py` or the background daemon invokes `/api/harden`, which exports tests to `test_hardened.py` in the workspace root. Similarly, running `tests/test_benchmarking.py` updates `benchmark_results.json`.
- **Remediation:**
  Update integration tests to use temporary directories (`tmp_path`) for exported test suites and benchmark JSON artifacts, keeping the Git working tree pristine.

---

## 3. Recommended Sequence Before Teacher Viva / Evaluation

1. **Address Finding H-01**: Wire `GranularTestValidator` into `testforge/corpus/runner.py` to ensure benchmark reports reflect true clean-passing mutant kills.
2. **Implement Milestone 4.1.3 (Finding M-02)**: Add shared context hoisting for complex test suites.
3. **Run Final Clean Full Suite**: Run `.venv-release/bin/python -m pytest tests/ -q` to confirm all 415+ tests pass with zero regressions.
4. **Prepare Live Demonstration Script**: Rehearse the live demo using `server.py` and the glassmorphic frontend (`frontend/index.html`).
