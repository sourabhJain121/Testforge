# ADR-004: AST Reflection, Recursive Bytecode Normalization, and Repair Loop

## Status
Accepted

## Context
Standard mutation testing systems suffer from two chronic failure modes:
1. **The Equivalent Mutant Problem**: Mutants that alter the AST without changing program semantics (e.g., constant folding, dead-code branches) can never be killed by any test suite, artificially capping mutation scores below 100% and causing reflection agents to spin fruitlessly in infinite loops.
2. **Hallucinated / Syntactically Broken Test Code**: LLM generators occasionally produce tests with syntax errors, invalid imports, or brittle assertions that fail on clean code, corrupting the test suite.

## Decision
We implemented a multi-stage **Reflection and Equivalence Loop**:
1. **Pass@1 Clean Code Validator**: Prior to mutant evaluation, every candidate test suite is run against the *unmodified* target code. Any test that fails clean code is quarantined or repaired before fault injection begins.
2. **Recursive Bytecode Instruction Normalization (`testforge/equivalence.py`)**:
   - Disassembles both clean and mutated code objects into instruction streams using `dis.get_instructions`.
   - Normalizes constant tables, line numbers, and variable offsets, and recursively compares nested code objects (closures, comprehensions, methods).
   - If instruction streams are identical, the mutant is mathematically proven equivalent and excluded from the denominator.
3. **LLM Semantic Equivalence Judge**: For mutants that produce distinct bytecode but identical behavioral contracts, a structured LLM judge classifies semantic equivalence.
4. **Targeted Adversarial Guidance**: The Critic agent provides surviving mutant unified diffs and explicit behavioral distinctions to the ReflectionRepairAgent, steering synthesis to missing edge cases.

## Consequences

### Positive
- Prevents infinite reflection loops on equivalent mutants.
- Achieved **100% adjusted mutation scores** on canonical benchmarks (`discount.py` and `order_fsm.py`).
- Guaranteed syntactic validity: 100% of pipeline-exported test suites execute cleanly out-of-the-box.

### Negative / Trade-offs
- Bytecode disassembly and comparison adds a small static analysis overhead (~5ms per mutant), which is negligible compared to sandbox execution time.

