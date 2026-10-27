# Phase 4.1.2 Acceptance Audit Report

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Semantic Guidance for Surviving Mutants & Finding M-01  
**Timestamp:** `20261026_123000`  
**Audit Type:** Independent Pre-Evaluation Acceptance Audit (Audit-Only, Read-Only)  
**Interpreter / Environment:** Python 3.11 (`.venv-release`), macOS Apple Silicon (arm64)  
**Overall Verdict:** **ACCEPT WITH FOLLOW-UP**

---

## 1. Executive Summary

An independent, rigorous audit was performed on Phase 4.1.2 ("Semantic Guidance for Surviving Mutants") to evaluate its architectural integrity, test coverage, safety rule adherence, and alignment with the 11 mandatory university teacher requirements before final evaluation.

### Key Audit Conclusions:
1. **Semantic Guidance Implementation**: **VERIFIED**. `testforge/guidance.py` cleanly extracts structured `SemanticMutantGuidance` records across all 10 mutation operators directly from AST nodes and unified diffs. Boundaries, off-by-one transitions, and non-zero operands are derived honestly. Confidence and uncertainty are strictly calibrated (`HIGH`, `MEDIUM`, `LOW`, `UNCERTAIN`).
2. **Finding M-01 Narrow Resolution**: **VERIFIED**. `GranularTestValidator.has_meaningful_assertions` successfully recognizes custom assertion helpers (`assert_*`, `verify_*`, `assert_never`) and preamble helper functions containing assertions, without accepting arbitrary non-assertion calls (`log_debug`, `ordinary_helper`).
3. **Pipeline Propagation & Candidate Re-evaluation**: **VERIFIED**. Guidance reaches both Generator and Critic agent execution paths, updates Blackboard (`CriticSpace.semantic_guidance`) and `TestForgeState`, and re-evaluates retained candidate tests against surviving mutants to confirm kills.
4. **Test Suite Integrity**: **VERIFIED**. 20/20 targeted tests pass in 9.38s. Related agentic and mutation suites pass (39/39 in 20.70s). The full repository test suite previously achieved 415/415 passing tests with zero regressions.
5. **Evaluation Validity Nuance (Finding H-01)**: The reported 100% mutation score across the 5 reference fixtures was subjected to adversarial scrutiny. In the production orchestrator (`orchestrator.py`), granular validation filters out candidate tests that fail on clean reference code. However, in the benchmark harness (`testforge/corpus/runner.py`), candidate suites were evaluated directly against mutants without first filtering false-positive tests and without passing `baseline_passed=(failed_ref == 0)`. When local LLM synthesis produced tests that failed against clean code, pytest failed on mutants as well, counting them as kills in the benchmark report. This finding is fully documented in `EVALUATION_VALIDITY.md`.

---

## 2. Workspace Integrity & Ephemeral File Investigation

### 2.1 Git Status & Safety Checks
- `git status --short`:
  ```
  M  .gitignore
   M benchmark_results.json
   M benchmark_results.md
   M test_hardened.py
   M testforge/agents.py
   M testforge/blackboard.py
   M testforge/corpus/runner.py
   M testforge/mutator.py
   M testforge/orchestrator.py
   M testforge/sandbox.py
   M testforge/state.py
  D  testforge_trace.jsonl
  D  trace_reflected.jsonl
  D  trace_zeroshot.jsonl
  ?? qa_artifacts/phase4_m1_adversarial_review_20261026_113400/
  ?? qa_artifacts/phase4_m1_implementation_20261026_112600/
  ?? qa_artifacts/phase4_m1_plan_20261026_103600/
  ?? qa_artifacts/phase4_m1_verification_20261026_112800/
  ?? qa_artifacts/phase4_m2_acceptance_audit_20261026_123000/
  ?? qa_artifacts/phase4_m2_semantic_guidance_20261026_121500/
  ?? qa_artifacts/post_push_integrity_verification_20261026_102200/
  ?? testforge/guidance.py
  ?? tests/test_mutation_guided_repair.py
  ```
- `git diff --check` and `git diff --cached --check`: Passed with zero whitespace errors or conflict markers.
- **Housekeeping Preservation**: Staged changes from Phase 3.1 (`.gitignore` update and 3 trace file index-only deletions) remain completely preserved and isolated in the index.
- **Commit / Push Status**: Zero commits and zero pushes were performed.

### 2.2 Investigation of Modified Ephemeral Files
1. **`test_hardened.py`**:
   - *Investigation*: Modified during integration test execution. `server.py:1311` (`/api/harden`) and `app.py:470` export the resulting test suite to `test_hardened.py` by default. When tests like `tests/test_fast_benchmarking.py` or background daemon processes ran against `samples/discount.py`, `test_hardened.py` was regenerated.
   - *Conclusion*: Confirmed as a test/daemon runtime side effect (previously identified as Finding L-02 in Phase 4.1.1). Preserved as-is without modification.
2. **`benchmark_results.json` and `benchmark_results.md`**:
   - *Investigation*: Updated when `tests/test_benchmarking.py` or `server.py` (`POST /api/benchmark/run`) executed a single baseline run on `samples/discount.py`.
   - *Conclusion*: Standard benchmark telemetry output files. Preserved as-is without modification.

---

## 3. Code Evidence Audit: Semantic Mutant Guidance

| Subsystem / Property | Code Location | Verified Behavior |
|---|---|---|
| **AST Derivation** | [`testforge/guidance.py:63-140`](file:///Users/sourabh/TestForge/testforge/guidance.py#L63-L140) | Derives guidance from `MutantRecord` AST node metadata and fallback diff inspection across all 10 mutation operators (`COMP_OP`, `BOUNDARY_SWAP`, `OFF_BY_ONE`, `ARITH_OP`, `LOGICAL_CONN`, `MATH_FUNC`, `COND_INV`, `RETURN_VAL`, `CONST_VAL`, `EXCEPT_HANDLER`). |
| **Confidence & Uncertainty** | [`testforge/guidance.py:130-140`](file:///Users/sourabh/TestForge/testforge/guidance.py#L130-L140) | Ambiguous or complex AST changes are assigned `confidence="UNCERTAIN"` with explicit uncertainty notes: *"Behavioral distinction cannot be reliably inferred statically from AST diff alone."* |
| **Critic Prompt & Fallback** | [`testforge/agents.py:761-817`](file:///Users/sourabh/TestForge/testforge/agents.py#L761-L817) | `AdversarialCriticAgent` consumes `surviving_mutants`, formats structured semantic guidance into prompts, and in offline/fallback mode generates numbered directives directly from guidance models. |
| **Generator Prompt Injection** | [`testforge/agents.py:427-432`](file:///Users/sourabh/TestForge/testforge/agents.py#L427-L432) | `TestGeneratorAgent` formats a dedicated `### Surviving Mutant Semantic Guidance` block into synthesis prompt kwargs. |
| **Blackboard & State Propagation** | [`testforge/blackboard.py:78`](file:///Users/sourabh/TestForge/testforge/blackboard.py#L78), [`testforge/state.py:84`](file:///Users/sourabh/TestForge/testforge/state.py#L84), [`testforge/orchestrator.py:1367-1390`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L1367-L1390) | Step F derives guidance, updates Blackboard `CriticSpace.semantic_guidance` and `failure_mechanisms`, and persists to `TestForgeState`. |
| **Candidate Re-evaluation** | [`testforge/sandbox.py:867-876`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L867-L876) | `GranularTestValidator.validate_candidate_suite` executes retained candidate tests against surviving mutants, recording confirmed kills in `mutants_killed`. |
| **M-01 Custom Assertion Resolution** | [`testforge/sandbox.py:443-490`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L443-L490) | `has_meaningful_assertions` accepts `assert_*`, `verify_*`, `assert_never`, and preamble helper definitions containing assertions. Rejects non-assertion helpers (`log_debug`, `ordinary_helper`). |

---

## 4. Test Evidence Summary

- **Focused Semantic Guidance Suite (`tests/test_mutation_guided_repair.py`)**:
  - Independent Run: **20 passed in 9.38s (Exit code 0)**.
  - Covers boundary conditions, arithmetic, math functions, unknown fallbacks, prompt propagation, blackboard propagation, M-01 helper resolution, ordinary helper rejection, and deterministic mutant killing.
- **Related Agentic & Mutation Suites (`tests/test_ast_mutation_m2.py`, `tests/test_crew_critic.py`, `tests/test_adk_generator.py`, `tests/test_agentic_pipeline.py`)**:
  - Independent Run: **39 passed in 20.70s (Exit code 0)**.
- **Full Repository Test Suite (`pytest tests/ -q`)**:
  - Previously reported: **415 passed, 4 warnings in 319.12s (Exit code 0)**.

---

## 5. Audit Findings Classification

### HIGH (Finding H-01) — Benchmark Runner Denominator / False Positive Disconnect
- **Issue**: In `testforge/corpus/runner.py:599`, `test_code_to_eval` was passed to `evaluate_mutants_parallel` without setting `baseline_passed = (failed_ref == 0)` and without running `GranularTestValidator`. When local LLM generation produced tests that failed against clean code, pytest exited non-zero across mutant runs, marking all mutants as "killed" in the benchmark report.
- **Impact**: While the production pipeline (`orchestrator.py`) filters false positives correctly, the empirical benchmark report overstates mutation scores on suites containing broken tests.
- **Recommendation**: Pass `baseline_passed = (failed_ref == 0)` in `testforge/corpus/runner.py` or filter candidate suites with `GranularTestValidator` before mutant evaluation in the benchmark runner.

### MEDIUM (Finding M-02) — Shared Module Context in Granular Validation
- **Issue**: Granular validation isolates individual test functions into standalone sandboxes with module preamble. If tests rely on shared mutable module globals, fixtures defined outside the preamble, or sequential state modified by another test, isolated execution may fail.
- **Recommendation**: Implement AST extraction for module-level assignments and shared `@pytest.fixture` definitions in Milestone 4.1.3.

### LOW (Finding L-02) — Side-Effects on Root Ephemeral Files
- **Issue**: Running test suites and background daemons updates `test_hardened.py`, `benchmark_results.json`, and `benchmark_results.md` in the workspace root.
- **Recommendation**: Configure integration tests to export to temporary paths (`tmp_path`) rather than the workspace root.

---

## 6. Audit Verdict

### Verdict: **ACCEPT WITH FOLLOW-UP**

Phase 4.1.2 meets all implementation, architectural, and safety requirements. The semantic guidance engine is fully operational, well-tested, and deeply integrated into the TestForge agent loop. Finding M-01 is definitively resolved. Acceptance is granted with recommended follow-up on benchmark runner false-positive handling (Finding H-01) and shared module context (Finding M-02) prior to teacher evaluation.
