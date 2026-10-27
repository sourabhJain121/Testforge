# TestForge Phase 4.1.1 — Known Limitations & Remaining Risks

**Timestamp**: 2026-10-26T11:28:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Scope**: Phase 4.1 Milestone 1 (Isolated Candidate Test Validation Verification)

---

## 1. Intentional Milestone Scope Boundaries

1. **Mutation Score Improvements Not Claimed**:
   - Milestone 1 establishes the candidate-test validation and quarantine mechanism.
   - It intentionally does not alter `AdversarialCriticAgent` prompts, AST mutators, or equivalence scoring rules.
   - Benchmark mutation score increases will be measured in subsequent milestones when semantic Critic directives are integrated.
2. **Semantic Critic Changes Deferred**:
   - The Critic currently passes unified diff strings. Translating `COMP_OP` and `BOUNDARY_SWAP` diffs into explicit input-boundary directives is scheduled for Milestone 2.
3. **Equivalence Rules Deferred**:
   - Equivalence checking in `testforge/equivalence.py` remains unchanged.

---

## 2. Technical Limitations & Edge Cases

1. **Sequential Inter-Test State Dependencies Across Batches**:
   - In rare cases where an LLM generates tests that depend on side-effects from preceding tests in the same file (e.g., modifying global state), running a single test in isolation will fail.
   - *Mitigation*: The validator first checks if the test passed during the full suite run. If so, it preserves the test as part of the reassembled suite.
2. **Subprocess Spawn Latency for Large Failing Batches**:
   - If an LLM generates 20 failing tests, running 20 individual subprocesses adds ~1–2s of execution time.
   - *Mitigation*: The fast-path optimization checks the entire suite first; isolated evaluation is only invoked when failures occur.
3. **Complex Module Imports with Cyclic Dependencies**:
   - If a test module imports from sibling test modules not present in the sandbox temporary directory, collection will fail.
   - *Mitigation*: Test modules are written against `target.py` in the sandbox root; collection errors are classified as `INFRASTRUCTURE_ERROR` without penalizing test validity.
