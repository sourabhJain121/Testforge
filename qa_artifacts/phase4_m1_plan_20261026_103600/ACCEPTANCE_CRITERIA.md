# TestForge Phase 4.1 — Quantitative Acceptance Criteria

**Timestamp**: 2026-10-26T10:36:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Purpose**: Measurable, unambiguous verification gates for the Phase 4.1 Mutation-Guided Test Improvement implementation.

---

## 1. Quantitative Verification Gates

| Category | Metric | Baseline (Zero-Shot) | Target Acceptance Threshold | Verification Method |
| :--- | :--- | :---: | :---: | :--- |
| **Defect Detection** | Controlled Defect Detection Rate | 66.7% (10/15) | **>= 93.3% (>= 14/15)** | Execution against 15 ground-truth defects in `CORPUS_REGISTRY`. |
| **Mutation Efficacy** | Raw Mutation Score | 67.8% | **>= 85.0%** across corpus | `calculate_mutation_scores` on all 201 generated AST mutants. |
| **Adjusted Efficacy**| Adjusted Mutation Score | 74.3% | **>= 92.0%** (target 100% on killable) | Excludes verified equivalent mutants (`evaluable - equivalent`). |
| **Clean Code Validity**| Original Implementation Pass Rate | 100.0% | **Strictly 100.0% (Zero false alarms)** | `SubprocessSandbox.run_single` against unmodified source code. |
| **Regression Safety** | Previously Killed Mutants Retained | N/A | **100% Retention (Zero regression)** | Differential kill matrix comparison between iteration $i$ and $i+1$. |
| **Flakiness & Determinism**| Repeatability across 3 runs | N/A | **100% Identical outcomes** | 3 consecutive runs under seed control with zero outcome flips. |
| **Iteration Bounds** | Maximum Repair Iterations | 1 | **<= 3 iterations** | Bounded in `TestForgeOrchestrator(max_iterations=3)`. |
| **Timeout Bounds** | Per-Iteration Hardening Timeout | N/A | **<= 60.0s per iteration** | Subprocess timeout guard with cancellation token check. |
| **Assertion Quality**| Avoidance of Trivial Assertions | N/A | **Zero non-substantive assertions** | AST lint filter rejecting `assert True`, `assert x is not None`. |

---

## 2. False Positive and False Negative Definitions

1. **False Positive (Test False Alarm)**:
   - A generated test that **fails** when executed against the correct, unmodified target implementation.
   - **Acceptance Criterion**: Strict 0 tolerance. Any test suite that fails against clean code is either repaired or rejected; it is never adopted as the active test suite.
2. **False Negative (Undetected Defect / Surviving Valid Mutant)**:
   - A mutant that introduces a behavioral deviation in the target code, but all generated tests continue to pass.
   - **Acceptance Criterion**: Reduced by at least 50% relative to Zero-Shot single-pass generation (from ~33% undetected to < 10% undetected).
3. **Equivalent Mutant Misclassification**:
   - A mathematically or semantically equivalent mutant wrongly flagged as an uncaught bug.
   - **Acceptance Criterion**: Rule-based AST equivalence filter must correctly classify static invariants (e.g. `x + 0` vs `x`, identical boolean short-circuits) before calculating adjusted scores.

---

## 3. Regression & Convergence Safety Rules

- **Rule 1 (Monotonic Quality Guard)**: If iteration $k+1$ produces a test suite with lower mutation score or lower line coverage than iteration $k$, the orchestrator must reject the candidate suite and retain iteration $k$.
- **Rule 2 (Clean Code Primacy)**: Under no circumstances may a test suite be accepted if it fails against the clean source code, even if it kills 100% of mutants.
- **Rule 3 (Bounded Budget)**: Total wall-clock time for the hardening loop must not exceed `max_iterations * 60s` (maximum 180s total). Total LLM token consumption must be tracked and bounded in `testforge_trace.jsonl`.
