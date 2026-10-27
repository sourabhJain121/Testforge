# Implementation & Remediation Plan: Restoring Agentic Reflection Superiority

**Date:** 2026-10-26T13:20:00+05:30  
**Target Milestone:** Phase 5.2 — Agentic Reflection Remediation  
**Status:** PROPOSED FIX PLAN (Read-Only Checkpoint — No Code Changes Made)

---

## 1. Prioritized Implementation Plan

The proposed remediation directly addresses the proven root causes identified in `DIAGNOSIS.md`, ordered by impact:

### Priority 1: Fix Benchmark Runner Suite Preservation & Retained Test Accounting
- **Files:** `testforge/corpus/runner.py`
- **Action:**
  1. In `_execute_strategy_run` for `agentic_reflection`, compute `retained_candidates` from the merged test suite (`test_code_to_eval`), or as:
     ```python
     test_code_to_eval = val_pass1.retained_test_code if val_pass1.retained_count > 0 else clean_v0
     # Count the actual test functions in test_code_to_eval
     retained_candidates = len(re.findall(r"def\s+test_\w+\s*\(", test_code_to_eval))
     ```
  2. Ensure `baseline_passed` remains `True` if `clean_v0` contained valid tests, even if Pass 1 generated zero new valid tests.
  3. Guarantee that Pass 1 failures never wipe out Pass 0 successes.

### Priority 2: Correct Deterministic Fallback Assertions for `convert_currency`
- **Files:** `testforge/agents.py`
- **Action:**
  1. Correct the mathematical constants in `_synthesize_ast_aware_tests` for `convert_currency`:
     - Change `assert convert_currency(100.0, "USD", "EUR") == 90.0` to `== 92.41`.
     - Change `assert convert_currency(1000.0, "USD", "EUR", is_vip=True) == 918.0` to `== 924.99`.
     - Remove erroneous `with pytest.raises(ValueError)` checks for `0.0` and `spread_bps=0`.
     - Test that the fallback test suite passes against `REFERENCE_CODE` with 100% precision.

### Priority 3: Optimize Local Ollama Timeout & Prevent Redundant Cascades
- **Files:** `testforge/llm_client.py`
- **Action:**
  1. Increase the local Ollama HTTP request timeout from 30.0s to 60.0s in `HybridLLMClient.generate`.
  2. If the user specified a primary local model (`qwen2.5-coder:7b`) and it is active, do not cascade across two additional 7B models (`qwen2.5:7b` and `codellama:7b`) if the prompt was valid; fail over cleanly without burning 90s in sequential timeouts.

### Priority 4: Provide Clean-Reference Execution Feedback to Generator in Pass 1
- **Files:** `testforge/agents.py`, `testforge/corpus/runner.py`, `testforge/orchestrator.py`
- **Action:**
  1. Add `quarantined_tests_feedback: Optional[List[Dict[str, str]]] = None` parameter to `TestGeneratorAgent.generate_tests`.
  2. In Pass 1, if any tests failed during Pass 0 validation, include a structured critique block:
     ```markdown
     ### Tests Quarantined Due to Assertion Errors against Clean Reference:
     - `test_compute_inventory_order_platinum_tier`: FAILED
       Reason: AssertionError: assert 550.0 == 725.0
       Guidance: Ensure bulk item discount ($2/item for qty >= 50) is subtracted after tier discount.
     ```
  3. This gives the LLM the ground-truth execution feedback needed to correct its mental arithmetic.

### Priority 5: Wire `AdversarialCriticAgent` into the Benchmark Runner
- **Files:** `testforge/corpus/runner.py`
- **Action:**
  1. Instantiate `AdversarialCriticAgent(logger=logger, api_key="")` in `_execute_strategy_run`.
  2. Invoke `critic.analyze_surviving_mutants(fixture.source_code, surviving_diffs, iteration=1, surviving_mutants=surviving[:3])`.
  3. Pass the resulting `critic_feedback` into `gen.generate_tests`.

---

## 2. Exact Files Likely to Change

| Target File | Expected Changes |
| :--- | :--- |
| `testforge/corpus/runner.py` | Fix `retained_candidates` accounting in Pass 1; preserve Pass 0 working suite; wire in `AdversarialCriticAgent`. |
| `testforge/agents.py` | Correct `convert_currency` fallback assertions; accept execution feedback in prompt; adjust system instruction for incremental repair. |
| `testforge/llm_client.py` | Increase Ollama timeout from 30s to 60s; optimize fallback retry order. |
| `tests/test_mutation_guided_repair.py` | Add unit tests verifying suite preservation when Pass 1 produces 0 valid tests. |

---

## 3. Regression Tests Required

1. **Suite Preservation Test:**
   - Define a test where Pass 0 produces 4 valid tests and Pass 1 produces a syntax/assertion error.
   - Verify that `validate_and_filter_candidate_suite` and `runner` retain the 4 valid tests.
   - Verify that `baseline_passed` is `True` and mutant kills reflect the 4 valid tests.
2. **Deterministic Fallback Validation Test:**
   - Execute `_synthesize_ast_aware_tests` for all 5 fixtures against their clean reference implementations.
   - Verify that 100% of fallback tests pass on clean code (0 false positives).
3. **Execution Feedback Test:**
   - Provide failed test assertion errors to `generate_tests`.
   - Verify that the feedback block is formatted properly into the LLM prompt.
4. **Full Test Suite:**
   - Run `.venv-release/bin/python -m pytest tests/ -q` ensuring 421/421 tests continue to pass.

---

## 4. Risks and Rollback Considerations

- **Non-Destructive Operations:** All changes will be made using standard file modification tools (`replace_file_content`). No `git reset`, `git clean`, or branch switching will be used.
- **Rollback Safety:** If any change causes a regression, specific replacement edits can restore the prior implementation without touching Git history or unrelated files.
- **Staged Housekeeping Isolation:** The 4 staged files from Phase 3.1 (`.gitignore` and trace deletions) will remain undisturbed in the Git index.

---

## 5. Measurable Acceptance Criteria

1. **Agentic Reflection Aggregate Superiority:**
   - Agentic Reflection mean mutation score must strictly exceed Zero-Shot across the 5 reference fixtures:
     $$\text{Mean Score}_{\text{agentic}} > \text{Mean Score}_{\text{zeroshot}} + 5.0\%$$
2. **Zero False-Regression on Fixture 5:**
   - On `currency_converter`, Agentic Reflection score must be $\ge 32.6\%$ (matching or exceeding Zero-Shot).
3. **Preservation Invariant:**
   - For every fixture, $\text{Score}_{\text{agentic}} \ge \text{Score}_{\text{pass0}}$, ensuring that a failed repair attempt can never degrade the working baseline score.
4. **Execution Latency Cap:**
   - Local Ollama agentic reflection runtime per fixture must not exceed 60.0s (eliminating 90s timeout cascades).
5. **Full Regression Stability:**
   - All 421 repository tests must pass with exit code 0.
