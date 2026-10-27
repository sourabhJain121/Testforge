# Known Limitations & Audit Tracking (Phase 4.1.3)

**Date:** 2026-10-26T12:50:00+05:30  
**Phase:** 4.1.3 — Benchmark Validity  
**Status:** Audit Finding H-01 RESOLVED

---

## 1. Resolution of Audit Finding H-01

- **Finding ID:** H-01 (from Phase 4.1.2 Independent Acceptance Audit)
- **Description:** Broken candidate test suites failing on clean reference code falsely killed mutants and yielded 100% mutation scores.
- **Resolution Status:** **FULLY RESOLVED**.
  - Candidate test suites are strictly filtered using `GranularTestValidator` to quarantine broken tests before mutant evaluation.
  - `evaluate_mutants_parallel` strictly requires `baseline_passed=True` before dispatching any mutant evaluations.
  - If the candidate test suite fails, times out, or has zero valid tests on the clean reference code, all mutants are classified as `ERROR` or `SURVIVED`, resulting in 0 kills and 0% mutation score.
  - Deterministic regression tests in `tests/test_mutation_guided_repair.py` verify that fails-original/fails-mutant never counts as a kill.

---

## 2. Tracking Remaining Audit Findings

### Finding M-02 (Medium Severity - Shared Context Leakage Across Iterations)
- **Status:** OPEN (Non-blocking for Phase 4.1.3 benchmark validity).
- **Description:** In multi-pass test generation loops, LLM chat session history is carried over, potentially biasing subsequent test generation or carrying hallucinated function signatures across iterations.
- **Impact:** Does not compromise the validity of the mutation benchmark scores, because all tests (regardless of how they were generated) are now rigorously filtered against clean reference code before mutant execution.
- **Recommended Follow-up:** Implement session memory clearing or stateless prompt templates for Critic and Repair agents in Phase 4.2.

---

## 3. Operational & Environmental Constraints

1. **Local LLM Model Specifics:**
   - Benchmark evaluation relies on local Ollama running `qwen2.5-coder:7b`.
   - On small or subtle fixtures, `qwen2.5-coder:7b` may occasionally generate hallucinated method calls (e.g. attempting to call unexported private helper methods). The granular test validator correctly quarantines these assertions, which may reduce the raw number of retained assertions but protects the benchmark from false kills.

2. **Equivalent Mutant Identification:**
   - Mutants classified as equivalent (e.g. Dead Code Mutation or AST equivalence) are excluded from the adjusted mutation score denominator as defined in `testforge/equivalence.py`.
   - Equivalent mutants that survive are not penalized in the adjusted mutation score.

3. **Subprocess Isolation:**
   - All candidate test execution runs inside temporary sandbox directories using `pytest` subprocesses with a 5-second timeout to prevent infinite loops from malicious or buggy tests.
