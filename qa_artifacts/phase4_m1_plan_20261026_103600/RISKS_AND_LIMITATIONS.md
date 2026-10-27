# TestForge Phase 4.1 — Risks, Limitations & Gap Analysis

**Timestamp**: 2026-10-26T10:36:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Purpose**: Document technical risks, theoretical limitations, and distinct classification of confirmed gaps vs. empirical hypotheses.

---

## 1. Confirmed Architectural Gaps vs. Empirical Hypotheses

### 1.1 Confirmed Code-Level Gaps (Verified in Source Code)
1. **All-or-Nothing Suite Rollback**:
   - *Code Location*: `testforge/orchestrator.py:1106-1118`.
   - *Observed Behavior*: If an LLM-generated hardened test suite contains 10 excellent new tests and 1 broken test that fails on clean code, `run_single` reports failure and the orchestrator discards the **entire** generated suite, rolling back completely to the prior iteration.
   - *Impact*: High waste of model tokens and missed opportunity to kill surviving mutants.
2. **Coarse Mutant Diff Presentation**:
   - *Code Location*: `testforge/orchestrator.py:1168-1172` & `testforge/agents.py:58-75`.
   - *Observed Behavior*: Surviving mutants are passed to the generator as raw unified diff strings without semantic input-output guidance (e.g., without identifying what inputs reach the line, what boundary conditions apply, or what public method exercises it).
   - *Impact*: The LLM frequently generates duplicate tests that hit already-covered branches instead of specifically targeting the mutated operator.
3. **Missing Per-Test Kill Attribution**:
   - *Code Location*: `testforge/sandbox.py:120-165`.
   - *Observed Behavior*: Mutants are marked `KILLED` if the pytest run exits with code 1, but the specific `test_xxx` function responsible for the kill is not indexed.
   - *Impact*: Inability to prune redundant or low-utility test functions, causing test suite bloat over successive iterations.

### 1.2 Hypotheses Requiring Experimental Validation
1. **Hypothesis 1 (Granular Test Pruning)**: Pruning individual broken test functions while retaining passing new tests will increase effective mutation score by >= 15% on difficult fixtures.
2. **Hypothesis 2 (Boundary-Focused Prompt Injection)**: Structuring critic directives with explicit boundary values (`<` vs `<=`, `0` vs `None`) will reduce surviving `BOUNDARY_SWAP` and `COMP_OP` mutants to zero without increasing suite execution time.
3. **Hypothesis 3 (Semantic Equivalent Mutant False Alarms)**: At least 5% of surviving mutants in arbitrary Python code are semantically equivalent and cannot be killed by any valid black-box test.

---

## 2. Technical Risks & Mitigation Strategies

| Risk | Description | Severity | Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **Mutant Overfitting** | Tests might assert internal variable names or hardcode mutant return values rather than validating functional requirements. | **HIGH** | Tests must execute against the public interface defined in AST function signatures and docstrings. Private attribute introspection is disallowed. |
| **Assertion Weakening** | LLMs attempting to make tests pass on both clean code and mutants might soften assertions (e.g. `assert res is not None`). | **HIGH** | AST assertion validator checks that assertions test equality, relational bounds, or explicit exception types, rejecting vacuous truthiness assertions. |
| **Clean Code False Alarm** | Generated test asserts an incorrect expectation, failing on the valid source code. | **CRITICAL** | Strict gate: Sandbox executes candidate tests against unmodified target code before mutation evaluation. If any test fails, it is quarantined. |
| **Equivalent Mutant Halting** | Program equivalence is undecidable in the general case (Rice's Theorem). | **MEDIUM** | Rule-based equivalence heuristics identify common static patterns; unverified mutants remain in the denominator of raw score, while adjusted score transparently documents exclusions. |
| **Token & Latency Inflation** | Complex reflection loops could exhaust token quotas or timeout. | **MEDIUM** | Enforce strict `max_iterations = 3`, per-iteration timeouts (60s), and fallback to deterministic AST synthesis if LLM calls fail. |
| **Execution Sandboxing Escapes** | Untrusted generated test code could perform unauthorized disk or network operations. | **HIGH** | Subprocess sandbox enforces strict timeouts, temporary directory isolation (`tmp_path`), and environment sanitization. |
