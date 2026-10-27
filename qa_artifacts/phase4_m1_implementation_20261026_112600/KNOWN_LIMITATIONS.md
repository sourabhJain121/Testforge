# TestForge Phase 4.1 — Milestone 1 Known Limitations & Scope Boundaries

**Timestamp**: 2026-10-26T11:26:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Scope**: Phase 4.1 Milestone 1 (Isolated Candidate Test Validation)

---

## 1. Intentional Milestone Scope Boundaries

1. **No Mutation-Score Claim for Milestone 1**:
   - Milestone 1 establishes the **safety harness** (granular validation, quarantine of broken tests, and test-suite merging) rather than measuring mutation score increases.
   - Empirical mutation score improvements will be measured in subsequent milestones when the semantic Critic and targeted mutation-guided prompting are active.
2. **Semantic Critic Changes Deferred to Milestone 2**:
   - `AdversarialCriticAgent` still receives unified diffs in this milestone. Enhancements translating `BOUNDARY_SWAP` and `COMP_OP` diffs into explicit input-output boundary values belong to Milestone 2.
3. **Equivalence Rule Expansion Deferred to Milestone 3**:
   - Static equivalence rules in `testforge/equivalence.py` remain unchanged in this milestone.

---

## 2. Technical Limitations & Edge Cases

1. **Inter-Test State Dependencies Across Candidate Batches**:
   - If candidate tests modify global or module-level variables sequentially (e.g., `test_b` depends on `test_a` having appended to an in-memory list), running `test_b` in complete isolation fails.
   - *Mitigation in Milestone 1*: The validator first checks whether the test passed in the full suite execution. If so, it preserves the test as part of the reassembled suite.
2. **Pytest Fixtures with `autouse=True`**:
   - Autouse fixtures defined in the preamble run for all isolated candidate tests. This is expected and intended, but fixtures with heavy I/O or external side-effects could introduce latency into isolated runs.
   - *Mitigation*: The fast-path optimization checks the full candidate suite first; isolated subprocess runs are only triggered when the candidate suite has at least one failure.
3. **Subprocess Overhead on Large Suites**:
   - For candidate suites with dozens of failing tests, validating each failing test individually in a separate subprocess incurs latency.
   - *Mitigation*: Parallel sandbox workers and per-test timeout bounds (default 3–5s) cap total validation time.
