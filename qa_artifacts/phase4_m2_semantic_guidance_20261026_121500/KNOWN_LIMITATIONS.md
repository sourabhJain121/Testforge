# Phase 4.1.2 Known Limitations & Future Work

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Semantic Guidance for Surviving Mutants & Finding M-01  
**Timestamp:** `20261026_121500`  

---

## 1. Static AST Heuristics vs. Dynamic Typing

The semantic guidance engine in `testforge/guidance.py` relies on static AST pattern matching to identify boundary values and discriminating inputs.

- **Assumption of Numeric / Primitive Domains**: For operators like `>` vs `>=`, the heuristic suggests testing `boundary`, `boundary - 1`, and `boundary + 1`. If the compared variable is an arbitrary domain object (e.g. custom classes, `datetime.date`, `Decimal`, or lexicographical strings), integer neighbor arithmetic (`boundary - 1`) cannot be evaluated literally without contextual adaptation by the test-generating agent.
- **Mitigation**: The guidance explicitly outputs the boundary condition concept (e.g. *"test exact equality at the boundary plus adjacent values"*) rather than forcing rigid literal constants, allowing the Critic and Generator to translate the directive to the appropriate domain type.

---

## 2. Path Reachability & Multi-Statement Preconditions

- **Localized Scope**: Semantic guidance analyzes the isolated AST node of the mutation (e.g. line 45: `if self.balance < amount:`).
- **Prefix Path Dependency**: In complex systems, reaching the mutated line may require specific setup sequences (e.g., authenticating a session, populating a cache, transitioning a state machine). The semantic guidance specifies *what condition must hold at the mutated site*, but does not perform full inter-procedural symbolic execution to synthesize the entire sequence of prior method calls.
- **Mitigation**: The Test Generator prompt combines both the source code context and the semantic guidance directive, enabling the LLM to synthesize the setup sequence while aiming for the targeted boundary value.

---

## 3. Equivalent Mutants & Rice's Theorem

- **Semantic Equivalence**: A surviving mutant may be semantically equivalent to the original program (e.g., an off-by-one check on an array whose length is guaranteed to be fixed, or defensive checks on unreachable conditions).
- **No Guarantee of Killability**: In accordance with project requirements, the guidance engine **never** claims a suggested input is guaranteed to kill a mutant without actual execution.
- **Uncertainty Calibration**: Ambiguous or complex AST transformations are marked with `confidence: "UNCERTAIN"` and explicit notes informing the Critic that the mutant may be equivalent or require domain investigation.

---

## 4. Custom Helper Analysis Depth (Finding M-01)

- **AST Preamble Traversal**: `GranularTestValidator.has_meaningful_assertions` inspects custom assertion helpers defined in the preamble or test file. If a helper calls a secondary helper that calls `assert`, nested inspection is bounded to prevent unbounded recursion or complex call graph evaluation during fast validation.
- **Naming Conventions**: Helpers named outside the `assert_*` or `verify_*` convention that are imported from external third-party libraries (rather than defined locally in the test preamble) may not be recognized as assertions unless explicitly defined or adhering to the naming prefix convention.

---

## 5. Shared Module Context & Fixtures (Finding M-02 Follow-Up)

- **Individual Test Execution**: Granular test validation extracts test functions and runs them in isolation with the module's `preamble_code`.
- **Limitation**: If candidate tests share mutable module globals, depend on autouse fixtures defined in external conftest files, or expect sequential execution order (e.g. test A writes state read by test B), isolated execution may fail.
- **Follow-Up**: Documented as Milestone 4.1.3 scope.
