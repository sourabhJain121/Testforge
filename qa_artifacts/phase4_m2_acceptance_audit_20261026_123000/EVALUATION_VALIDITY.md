# Evaluation Validity Audit: Analysis of the Reported 100% Mutation Score

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Semantic Guidance for Surviving Mutants  
**Timestamp:** `20261026_123000`  
**Subject:** Empirical Benchmark Corpus Evaluation (`qa_artifacts/phase4_m2_semantic_guidance_20261026_121500/BASELINE_COMPARISON.md`)

---

## 1. Executive Summary

In Phase 4.1.2 Step E, an empirical comparison of three strategies (Baseline, Zero-Shot, and Agentic Reflection with Semantic Guidance) was conducted across the 5 canonical corpus fixtures:
- `task_state_transition`
- `token_bucket_rate_limiter`
- `inventory_pricing_calculator`
- `banking_operations_module`
- `currency_converter`

The report documented that **Agentic Reflection** achieved a **100.0% mutation score** across all 5 fixtures (killing 201/201 generated evaluable mutants).

This audit investigated the underlying execution harness, AST mutant generation, candidate suite synthesis, and scoring math to determine whether this 100% result represents genuine mutant discrimination or an artifact of the evaluation harness.

---

## 2. Audit of the 7 Required Questions

### Question 1: Did all strategies evaluate the same fixture set and comparable mutant sets?
- **Finding:** **YES**.
- **Evidence:** All 3 strategies evaluated the identical 5 fixtures from `get_corpus_fixtures()`. For each fixture, `ASTMutator.generate_mutants(fixture.source_code)` was called identically, producing identical mutant counts:
  - `task_state_transition`: 57 mutants
  - `token_bucket_rate_limiter`: 38 mutants
  - `inventory_pricing_calculator`: 37 mutants
  - `banking_operations_module`: 23 mutants
  - `currency_converter`: 46 mutants
  - **Total**: Exactly 201 mutants generated for each strategy.

### Question 2: Did baseline, zero-shot, and agentic reflection use the same scoring definitions?
- **Finding:** **YES**.
- **Evidence:** All 3 strategies invoked `calculate_mutation_scores(evaluated)` from `testforge.equivalence`. Raw mutation score is calculated as:
  $$\text{Raw Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Mutants} - \text{Invalid Mutants}} \times 100.0$$
  In this run, 0 mutants were invalid AST syntax and 0 were classified as equivalent, so the evaluable denominator equaled the total mutants (201).

### Question 3: Were handwritten baseline tests evaluated against the same mutants as generated tests?
- **Finding:** **YES**.
- **Evidence:** Handwritten baseline tests were evaluated against the exact same AST mutants. Baseline killed 41/57 (71.9%), 31/38 (81.6%), 27/37 (73.0%), 18/23 (78.3%), and 36/46 (78.3%), leaving mutants surviving on every fixture.

### Question 4: Did the agentic strategy actually use semantic guidance during repair?
- **Finding:** **YES**.
- **Evidence:** In `testforge/corpus/runner.py:540-550`:
  ```python
  surviving = [m for m in eval_pass0 if m.status == "SURVIVED"]
  surviving_diffs = [m.unified_diff for m in surviving[:3]]
  surviving_guidance = derive_guidance_for_surviving_mutants(surviving[:3], target_code=fixture.source_code)
  synth_v1 = gen.generate_tests(
      source_code=fixture.source_code,
      surviving_diffs=surviving_diffs,
      iteration=1,
      surviving_guidance=surviving_guidance
  )
  ```
  The test generator prompt received the structured boundary conditions, operand distinctions, and off-by-one suggestions derived by `testforge/guidance.py`.

### Question 5: Did deterministic fallback logic or local Ollama generation contribute to the reported result?
- **Finding:** **YES (Primary driver was local Ollama `qwen2.5-coder:7b` with selective Tier 4 fallback)**.
- **Evidence:** Review of `task-9984.log` shows 13 test suites were synthesized live by the local Ollama engine (`qwen2.5-coder:7b` via port 11434), and 2 suites engaged the Tier 4 deterministic rule synthesizer.

### Question 6: Were any mutants excluded, marked equivalent, or omitted from denominators?
- **Finding:** **NO**.
- **Evidence:** No mutants were excluded or omitted. All 201 mutants were included in the denominator for all 3 strategies.

### Question 7: Are benchmark results reproducible and are any output files overwritten as side effects?
- **Finding:** **REPRODUCIBLE, WITH EPHEMERAL OVERWRITE SIDE-EFFECTS**.
- **Evidence:** The benchmark is deterministic and reproducible. However, when run without an explicit `--output-json` or isolated `trace_dir`, it updates root telemetry files (`benchmark_results.json`, `test_hardened.py`).

---

## 3. In-Depth Root Cause Analysis: The 100% Score Anomaly (Finding H-01)

While all 7 structural questions confirm that identical fixtures, mutant sets, and scoring formulas were used, an adversarial inspection of `testforge/corpus/runner.py` revealed a **critical evaluation validity defect**:

### 3.1 The Production Pipeline vs. The Benchmark Harness
1. **Production Pipeline (`testforge/orchestrator.py`)**:
   In the main TestForge pipeline, candidate tests are passed through `GranularTestValidator.validate_and_filter_candidate_suite`. This validator runs every candidate test against the clean reference code first. Any candidate test that fails against clean code is **quarantined and discarded**. Only valid, clean-passing tests are retained and evaluated against mutants.
2. **Benchmark Harness (`testforge/corpus/runner.py`)**:
   In `testforge/corpus/runner.py:599`, `test_code_to_eval` was evaluated against all mutants using:
   ```python
   mutants = ASTMutator.generate_mutants(fixture.source_code)
   evaluated = runner.evaluate_mutants_parallel(test_code_to_eval, mutants)
   ```
   Crucially, `test_code_to_eval` was **NOT** filtered through `GranularTestValidator` before mutant evaluation, and `evaluate_mutants_parallel` was called with the default parameter:
   ```python
   def evaluate_mutants_parallel(self, test_code: str, mutants: List[MutantRecord], baseline_passed: bool = True)
   ```

### 3.2 The Mechanism of False Mutant "Kills"
1. Local Ollama (`qwen2.5-coder:7b`) generates comprehensive candidate test suites. However, like most LLMs, it hallucinated non-existent methods or assertions that failed on clean reference code.
2. This is recorded in the benchmark output as `tests_failed_on_reference`:
   - `task_state_transition`: 7 failing tests on clean code
   - `token_bucket_rate_limiter`: 7 failing tests on clean code
   - `inventory_pricing_calculator`: 12 failing tests on clean code
   - `banking_operations_module`: 4 failing tests on clean code
   - `currency_converter`: 7 failing tests on clean code
3. When `runner.evaluate_mutants_parallel(test_code_to_eval, mutants)` executed the suite against each mutant in a sandboxed subprocess:
   - Pytest executed the entire file, including the failing tests.
   - Because the suite contained tests that fail on clean code, pytest exited with `status == "FAIL"` (returncode 1).
   - In `testforge/sandbox.py:276`:
     ```python
     elif result.get("status") == "FAIL" and result.get("tests_failed", 0) > 0:
         mutant.status = "KILLED"
     ```
   - Because `baseline_passed` was defaulted to `True`, the sandbox concluded that the test suite detected the mutation and marked the mutant as `KILLED`.
   - Consequently, **every mutant was marked killed**, resulting in an artificial 100.0% mutation score.

### 3.3 Contrast with Genuine Evaluations
- **Token Bucket Zero-Shot Run**: On `Token Bucket Rate Limiter` during zero-shot synthesis, the LLM generated 8 tests, and all 8 passed on clean reference code (`tests_failed_on_reference == 0`). On that run, the mutation score was a genuine **42.1% (16/38 killed)**.
- **Deterministic Unit Test**: In `tests/test_mutation_guided_repair.py:test_surviving_mutant_killed_after_repair_deterministic`, the candidate repair test was explicitly verified to pass clean reference code and fail only on the mutated code, proving that semantic guidance can genuinely kill surviving boundary mutants when properly filtered.

---

## 4. Threats to Validity Summary

1. **Construct Validity**: The mutation score metric in `testforge/corpus/runner.py` suffers from construct invalidity when `tests_failed_on_reference > 0`. A mutant cannot be considered killed by a test that fails on the clean program.
2. **Internal Validity**: The production pipeline (`orchestrator.py`) has the correct filtering logic (`GranularTestValidator`), but the standalone benchmark harness (`runner.py`) did not invoke it.
3. **External Validity**: Demonstrating a 100% mutation score across all 5 fixtures in a teacher evaluation without disclosing this harness defect would risk immediate disqualification.

---

## 5. Recommended Remedy for Teacher Evaluation

To ensure total academic and technical honesty during teacher evaluation:
1. In `testforge/corpus/runner.py:599`, filter `test_code_to_eval` through `GranularTestValidator.validate_candidate_suite` before mutant evaluation, or pass `baseline_passed = (failed_ref == 0)`.
2. Present the benchmark scores with explicit filtering disclosures: show the raw mutation score of clean-retained tests alongside the false-positive rejection rate.
3. Highlight that the granular test validator was designed precisely to solve this problem by quarantining broken candidate tests.
