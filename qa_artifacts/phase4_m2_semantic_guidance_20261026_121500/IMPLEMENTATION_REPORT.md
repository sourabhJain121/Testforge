# Phase 4.1.2 Implementation Report — Semantic Guidance for Surviving Mutants

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Semantic Guidance for Surviving Mutants & Finding M-01  
**Timestamp:** `20261026_121500`  
**Execution Environment:** Python 3.11 (`.venv-release`), Local Deterministic + Local Model (`qwen2.5-coder:7b`)

---

## 1. Executive Summary

Phase 4.1.2 transforms mutation-guided test repair in TestForge from raw unified diff string matching into a structured, semantic guidance system. Previously, surviving mutants were surfaced to the test generation and Critic agents only as raw textual diffs (e.g. `- x >= 10` / `+ x > 10`), forcing the LLM to guess the boundary condition or failing inputs through unguided trial and error.

This milestone introduces:
1. **Semantic Guidance Extraction (`testforge/guidance.py`)**: A dedicated module that analyzes AST mutant metadata and AST structures to produce structured `SemanticMutantGuidance` records capturing exact original/mutated expressions, source line, behavioral distinction, suggested boundary/discriminating inputs, and calibrated confidence (`HIGH`, `MEDIUM`, `LOW`, `UNCERTAIN`).
2. **End-to-End Orchestrator & Agent Integration**: Structured guidance is populated on Blackboard `CriticSpace`, tracked in `TestForgeState`, passed directly into `AdversarialCriticAgent` prompts and offline fallback directives, passed into `TestGeneratorAgent` prompts, and fed into benchmark runners.
3. **Surviving Mutant Re-evaluation in Sandboxes**: `GranularTestValidator` now accepts surviving mutants and executes each valid candidate test function against both clean code and surviving mutants, verifying whether candidate tests actually kill the intended mutants before suite inclusion.
4. **Narrow Resolution of Adversarial Review Finding M-01**: Custom assertion helpers (`assert_*`, `verify_*`, or preamble helper functions containing assertions) are recognized by `GranularTestValidator.has_meaningful_assertions` so modular test suites delegating checks are not falsely rejected as `TRIVIAL_NO_ASSERTIONS`, while non-verifying helpers (logging, mathematical helpers) remain strictly rejected.

---

## 2. Step A: Traced Pipeline Flow & Architecture

Before implementation, the repository code path from mutant creation to repair re-evaluation was traced across existing components:

```
[Target Source Code]
        │
        ▼
[ASTMutator.generate_mutants()] ───> Generates MutantRecord objects (AST diff, op_type, line, node)
        │
        ▼
[ParallelSandboxRunner.evaluate_mutants_parallel()] ───> Executes test suite in worker pools
        │
        ├──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼
  [KILLED Mutants]      [INVALID Mutants]     [SURVIVING Mutants]
                                                      │
                                                      ▼
                                       [derive_guidance_for_surviving_mutants()]
                                                      │
                                                      ▼
                                           [SemanticMutantGuidance]
                                                      │
                     ┌────────────────────────────────┴────────────────────────────────┐
                     ▼                                                                 ▼
      [CriticSpace / TestForgeState]                                      [AdversarialCriticAgent]
     (Blackboard shared state update)                                     (Injects boundary directives)
                     │                                                                 │
                     └────────────────────────────────┬────────────────────────────────┘
                                                      ▼
                                           [TestGeneratorAgent]
                                     (Synthesizes targeted test functions)
                                                      │
                                                      ▼
                                   [GranularTestValidator.validate_candidate_suite()]
                                     - AST syntax & purity check
                                     - M-01 custom helper resolution
                                     - Execution on clean reference code
                                     - Execution on surviving mutants (Killed verification)
                                                      │
                                                      ▼
                                      [Retained Suite / State Update]
```

### Verified Code Paths:
1. **Mutant Representation**: `MutantRecord` in `testforge/mutator.py` captures `mutant_id`, `operator_name`, `line_number`, `original_code`, `mutated_code`, `unified_diff`, and AST node metadata.
2. **Identification of Surviving Mutants**: Executed in `ParallelSandboxRunner.evaluate_mutants_parallel()`, returning records where `status == "SURVIVED"`.
3. **Blackboard / State Updates**: `CriticSpace` in `testforge/blackboard.py` and `TestForgeState` in `testforge/state.py` now store `semantic_guidance: List[Dict[str, Any]]` alongside `failure_mechanisms` and `adversarial_critique`.
4. **Critic & Generator Prompt Construction**:
   - `AdversarialCriticAgent.analyze_surviving_mutants(surviving_mutants=...)`: Converts surviving mutants into formatted semantic guidance directives and embeds them in the LLM prompt. In offline/fallback mode, generates structured directives directly from the guidance models.
   - `TestGeneratorAgent.generate_tests(surviving_guidance=...)`: Embeds a dedicated `### SEMANTIC MUTANT GUIDANCE & BOUNDARY CONDITIONS` block in the test synthesis prompt with exact boundary values.
5. **Candidate-Test Validation & Re-evaluation**:
   - `ParallelSandboxRunner.validate_and_filter_candidate_suite(surviving_mutants=...)`: Invokes `GranularTestValidator.validate_candidate_suite`, parsing individual functions, checking preamble helpers, running clean isolation tests, and running mutated isolation tests to record `mutants_killed`.

---

## 3. Step B: Semantic Guidance Implementation (`testforge/guidance.py`)

A new module [testforge/guidance.py](file:///Users/sourabh/TestForge/testforge/guidance.py) was created providing:

### 3.1 Data Model: `SemanticMutantGuidance`
```python
class SemanticMutantGuidance(BaseModel):
    mutant_id: str
    mutation_type: str
    original_expression: str
    mutated_expression: str
    line_number: Optional[int] = None
    behavioral_distinction: str
    suggested_inputs: List[str] = Field(default_factory=list)
    confidence: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW", "UNCERTAIN"
    uncertainty_notes: Optional[str] = None
```

### 3.2 Supported Mutation Operators & Heuristics
The derivation engine inspects both `MutantRecord` objects and serialized dictionary representations:

1. **Comparison Mutations (`COMP_OP`, `BOUNDARY_SWAP`)**:
   - `>` vs `>=`: Boundary point is tested at exact equality (`x == boundary`), plus off-by-one neighbors (`boundary - 1`, `boundary + 1`). Confidence: `HIGH`.
   - `<` vs `<=`: Boundary point tested at exact equality, plus off-by-one neighbors. Confidence: `HIGH`.
   - `==` vs `!=`: Tests matching value (where original is True) and distinct value (where original is False). Confidence: `HIGH`.
2. **Off-by-One Mutations (`OFF_BY_ONE`)**:
   - `+ 1` / `- 1` replacements: Distinguishes step boundaries by asserting exact expected index/count before and after transition. Confidence: `HIGH`.
3. **Arithmetic Operator Replacement (`ARITH_OP`)**:
   - `+` vs `-`: Distinguishes with non-zero operand (`b != 0`, e.g. `b = 1`, `b = -1`, `b = 2`).
   - `*` vs `/`: Distinguishes with operands other than 1 and 0.
   - `*` vs `**`: Distinguishes with values where $a \cdot b \neq a^b$ (e.g. `a=2, b=3`). Confidence: `MEDIUM` to `HIGH`.
4. **Logical Connectors (`LOGICAL_CONN`)**:
   - `and` vs `or`: Tests asymmetric inputs where left is False and right is True (`(False, True)`), or left is True and right is False (`(True, False)`). Confidence: `HIGH`.
5. **Math Built-ins (`MATH_FUNC`)**:
   - `min` vs `max`: Tests unequal arguments (`a != b`) where one strictly exceeds the other. Confidence: `HIGH`.
6. **Condition Inversion (`COND_INV`)**:
   - Tests both truthy and falsy states of the condition to reveal inverted control flow. Confidence: `HIGH`.
7. **Return Value Modifications (`RETURN_VAL`)**:
   - Distinguishes boolean flips (`True` vs `False`) and None replacements. Confidence: `HIGH`.
8. **Constant Values (`CONST_VAL`)**:
   - Replaces literal constants (e.g. 0 vs 1, strings); suggests checking outputs that compute on or depend on the exact constant. Confidence: `MEDIUM`.
9. **Exception Handlers (`EXCEPT_HANDLER`)**:
   - Mutated exception types; suggests triggering the specific exception to observe propagation vs capture. Confidence: `MEDIUM`.
10. **Ambiguous / Fallback Mutations**:
   - When expressions cannot be safely parsed from diff or AST, provides cautious descriptive guidance with confidence `UNCERTAIN` and explicit caveats: *"Never assume suggested inputs guarantee a kill without test execution."*

---

## 4. Step C: Resolution of Finding M-01 (Custom Assertion Helpers)

### 4.1 Vulnerability Description
Adversarial review finding M-01 identified that `GranularTestValidator.has_meaningful_assertions` previously performed a rigid AST search for `ast.Assert` statements only. Well-architected test suites that delegate assertions to domain-specific helpers (e.g., `assert_valid_order(order)` or `verify_rate_limit(limiter)`) were falsely flagged as `TRIVIAL_NO_ASSERTIONS` and discarded.

### 4.2 Narrow Resolution
In [testforge/sandbox.py](file:///Users/sourabh/TestForge/testforge/sandbox.py):
1. **Assertion Naming Conventions**: Evaluates function calls against recognized assertion naming conventions:
   - Call name starts with `assert_` (e.g., `assert_valid_token`, `assert_balance`).
   - Call name starts with `verify_` (e.g., `verify_state_change`).
   - Call name is `assert_never`.
2. **Preamble Function Body Analysis**: When helper functions are defined in the module preamble or test suite context (`helper_defs`), the validator parses their AST bodies. If the body contains an `ast.Assert` or nested assertion call, any test function invoking that helper is accepted.
3. **Strict Rejection of Non-Verifying Helpers**: Function calls like `print(x)`, `log_debug(order)`, `calculate_tax(100)`, or `ordinary_helper(5)` that do not meet the naming standard and do not contain assertions in their definition are **strictly rejected** as trivial tests.

---

## 5. Summary of Files Changed

| File | Status | Description |
|---|---|---|
| `testforge/guidance.py` | New File | `SemanticMutantGuidance` model, operator heuristics, guidance formatters. |
| `testforge/sandbox.py` | Modified | M-01 custom helper resolution, surviving mutant execution in candidate validation. |
| `testforge/orchestrator.py` | Modified | Semantic guidance derivation in Step F, injection into generator/critic in Step A & F. |
| `testforge/agents.py` | Modified | Prompt templates and offline logic consuming semantic guidance. |
| `testforge/blackboard.py` | Modified | `CriticSpace.semantic_guidance` field addition. |
| `testforge/state.py` | Modified | `TestForgeState.semantic_guidance` field addition. |
| `testforge/mutator.py` | Modified | Export guidance utilities from mutator module. |
| `testforge/corpus/runner.py` | Modified | Passes `surviving_guidance` to `agentic_reflection` strategy runs. |
| `tests/test_mutation_guided_repair.py` | Modified | 10 comprehensive deterministic unit & regression tests. |

All changes maintain 100% backward compatibility with existing Blackboard conventions, API contracts, and CLI interfaces.
