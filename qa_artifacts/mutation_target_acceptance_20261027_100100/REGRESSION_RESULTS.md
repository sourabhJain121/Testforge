# TESTFORGE AUTOMATED REGRESSION RESULTS

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/mutation_target_acceptance_20261027_100100/`  
**Timestamp:** `2026-10-27T10:21:00+05:30`  
**Python Environment:** `.venv-release/bin/python` (Python 3.13.18, macOS darwin arm64)  
**Pytest Version:** pytest 9.1.1, pluggy 1.7.0

---

## 1. Focused Unit & UI Contract Tests

### Command:
```bash
.venv-release/bin/python -m pytest tests/test_mutation_scores.py -v
```

### Result:
```
============================= test session starts ==============================
platform darwin -- Python 3.13.18, pytest-9.1.1, pluggy-1.7.0 -- /Users/sourabh/TestForge/.venv-release/bin/python
cachedir: .pytest_cache
rootdir: /Users/sourabh/TestForge
plugins: cov-7.1.0, anyio-4.15.1, platformdirs-4.13.5
collecting ... collected 9 items

tests/test_mutation_scores.py::test_zero_eligible_mutants PASSED         [ 11%]
tests/test_mutation_scores.py::test_all_mutants_killed PASSED            [ 22%]
tests/test_mutation_scores.py::test_surviving_mutants_partial_score PASSED [ 33%]
tests/test_mutation_scores.py::test_equivalent_mutants_adjusts_denominator PASSED [ 44%]
tests/test_mutation_scores.py::test_all_surviving_are_equivalent_gives_100_percent_adjusted PASSED [ 55%]
tests/test_mutation_scores.py::test_invalid_and_errored_mutants_excluded PASSED [ 66%]
tests/test_mutation_scores.py::test_potentially_equivalent_recorded_explicitly PASSED [ 77%]
tests/test_mutation_scores.py::test_target_score_verdict_distinction PASSED [ 88%]
tests/test_mutation_scores.py::test_frontend_app_js_status_contract_truthfulness PASSED [100%]

============================== 9 passed in 0.08s ===============================
```
- **Exit Code:** `0`
- **Result:** 9 passed, 0 failed.

---

## 2. Full Regression Suite Execution

### Command:
```bash
.venv-release/bin/python -m pytest tests/ -q
```

### Output:
```
......................................................................   [100%]
=============================== warnings summary ===============================
(346 library deprecation warnings from CrewAI, FastAPI on_event, and Starlette)
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
430 passed, 346 warnings in 259.40s (0:04:19)
```

### Summary of Full Run:
| Metric | Value | Status |
| :--- | :--- | :---: |
| **Total Tests Discovered** | 430 | ✅ |
| **Passed Tests** | 430 | ✅ |
| **Failed Tests** | 0 | ✅ |
| **Errors** | 0 | ✅ |
| **Skipped** | 0 | ✅ |
| **Duration** | 259.40s (4m 19s) | ✅ |
| **Pytest Exit Code** | `0` (SUCCESS) | ✅ |

### Deprecation Warnings Breakdown:
The 346 warnings emitted during the full test suite are third-party upstream deprecation notices from:
1. `fastapi`: `@app.on_event("startup")` deprecated in favor of FastAPI lifespan handlers.
2. `crewai`: `function_calling_llm` and `allow_code_execution` warnings in CrewAI agent core.
3. `starlette`: `anyio.abc.BlockingPortal` alias warning.
4. `google.cloud.aiplatform`: future warning regarding `google-cloud-storage < 3.0.0`.

None of these warnings stem from TestForge test orchestration logic, and none affect runtime stability.

---

## 3. Regression Verdict

Zero regressions detected across all 430 automated test cases. All new UI contracts and mutation score calculations pass cleanly.
