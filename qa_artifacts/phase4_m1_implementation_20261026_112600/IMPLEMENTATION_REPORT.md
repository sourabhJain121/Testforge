# TestForge Phase 4.1 — Milestone 1 Implementation Report: Granular Generated-Test Validation

**Timestamp**: 2026-10-26T11:26:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Milestone**: Phase 4.1, Milestone 1 — Granular Candidate Test Validation  
**Status**: Implemented & Verified (All 405 Tests Passing)

---

## 1. Executive Summary

Milestone 1 resolves the **all-or-nothing candidate suite rollback gap** (`Gap 1` from the Phase 4.1 plan). Previously, if an LLM-synthesized test suite contained 9 high-value tests and a single broken assertion, the entire candidate suite was discarded, and the orchestrator rolled back completely to the prior iteration.

We implemented `GranularTestValidator` in `testforge/sandbox.py` and updated `TestForgeOrchestrator._execute_pipeline` in `testforge/orchestrator.py` to validate candidate test functions individually against clean target code. Confirmed valid tests are retained and merged into the active suite, while only confirmed failing candidates or vacuous tests are quarantined.

---

## 2. Modified & Created Files

| File | Change Type | Purpose |
| :--- | :---: | :--- |
| `testforge/sandbox.py` | Modified | Added `GranularTestValidator`, `TestValidationStatus`, `TestFunctionRecord`, `CandidateSuiteValidationResult`, and `validate_and_filter_candidate_suite` method on `ParallelSandboxRunner`. |
| `testforge/orchestrator.py` | Modified | Updated reflection loop (lines 1104–1120) to invoke `validate_and_filter_candidate_suite`, merging retained valid tests while quarantining failing tests without discarding the suite. |
| `tests/test_mutation_guided_repair.py` | Created | New dedicated test suite covering all 10 scenario requirements (10/10 passed). |

---

## 3. Detailed Component Architecture

### 3.1 `GranularTestValidator` (`testforge/sandbox.py`)
1. **Module Context Extraction (`split_test_module`)**:
   - Parses the candidate module via Python's `ast` module.
   - Separates preamble statements (docstrings, imports, constants, `@pytest.fixture` functions, setup helpers) from test functions (`def test_*`) and test classes (`class Test*`).
   - Ensures no test function is executed in isolation without its required imports, fixtures, and constants.
2. **Assertion Quality Screening (`has_meaningful_assertions`)**:
   - Analyzes AST nodes for substantive assertions.
   - Rejects trivial assertions (`assert True`, `assert 1`, `assert not False`, or functions with no assertions/exception checks).
   - Recognizes context manager exception checks (`with pytest.raises(...)`, `with pytest.warns(...)`) and `unittest`-style assertions (`self.assertEqual`).
3. **Execution Routing & Fast-Path Optimization**:
   - Executes the full candidate suite first. If all candidate tests pass against the clean target code, they are accepted immediately without spawning multiple subprocesses.
   - If collection fails due to missing imports or environment errors, it is classified as `INFRASTRUCTURE_ERROR` without misclassifying tests as assertion failures.
   - If tests fail, it evaluates candidate tests individually with full preamble context in the sandbox.
4. **Classification & Quarantine**:
   - `VALID`: Passed clean target check with substantive assertions.
   - `FAILING`: Failed assertion against clean target code.
   - `TIMEOUT`: Exceeded sandbox timeout (e.g. infinite loop caught; inconclusive).
   - `INFRASTRUCTURE_ERROR`: Module/import/environment error (inconclusive).
   - `TRIVIAL_NO_ASSERTIONS`: Zero substantive assertions.
5. **Safe Reassembly & Merging (`merge_test_suites`)**:
   - Reassembles retained valid tests with preamble.
   - Merges with existing accepted test suite, combining imports/fixtures and augmenting existing test functions.
   - Re-verifies merged code in sandbox before returning.

### 3.2 Orchestrator Integration (`testforge/orchestrator.py`)
In `_execute_pipeline`:
- Replaced the binary `if clean_check["status"] == "PASS": current = hardened else: retain` logic with:
  ```python
  validation_res = self.sandbox.validate_and_filter_candidate_suite(
      candidate_test_code=hardened_tests,
      target_code=self.state.target_source_code,
      existing_test_code=self.state.current_test_code
  )
  if validation_res.retained_count > 0 and validation_res.retained_test_code:
      self.state.current_test_code = validation_res.retained_test_code
      # Logs retained vs quarantined counts to console and Blackboard
  ```
- If all candidates fail or time out, the existing suite is preserved intact.

---

## 4. Safeguards Enforced

- **Clean Target Invariance**: Clean source code is never altered or relaxed to accommodate candidate tests.
- **Context Preservation**: Test functions are always executed with all module-level imports, fixtures, and helpers.
- **No Inconclusive Misclassification**: Subprocess timeouts and infrastructure collection errors are flagged as inconclusive and quarantined, never reported as failed assertions.
- **Backward Compatibility**: `SubprocessSandbox.run_single` and standard test workflows remain 100% backward-compatible.
