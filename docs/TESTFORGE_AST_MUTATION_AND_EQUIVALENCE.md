# TestForge — Milestone 2: AST-Aware Mutation & Equivalent-Mutant Analysis Architecture

**Author**: Sourabh & Shreshth  
**Course**: Autonomous Agentic AI  
**Repository**: `/Users/sourabh/TestForge`  
**Milestone**: Milestone 2  
**Verification Environment**: Python 3.13.1 (`.venv-release`)  
**Hardware Profile**: Apple Silicon M2 Pro (10 CPU cores)  

---

## 1. Executive Summary

Milestone 2 advances TestForge from basic syntactic fault injection into a **rigorous, deterministic, syntax-aware AST mutation testing and conservative equivalent-mutant analysis platform**. 

Key enhancements delivered in Milestone 2:
1. **10 Deterministic AST Mutation Operators**: Implemented via Python's `ast` module and `ast.NodeTransformer` with full expression provenance, non-destructive in-memory transformations, and AST compilation validation.
2. **Conservative Equivalent-Mutant Analysis Layer**: Introduced `testforge/equivalence.py` providing static and heuristic equivalence detection across provable categories (syntactic AST identity, dead code elimination, algebraic identity transforms) and heuristic domain invariants (`len(x) >= 0`), strictly resisting false positives.
3. **Explicit Mutation Score Formulas**: Formalized raw mutation scores vs. adjusted mutation scores (excluding verified equivalent mutants) while strictly removing invalid syntax and infrastructure errors from the evaluable denominator.
4. **Partition State & Checkpoint Persistence**: Seamlessly integrated new mutant metadata into `MutantRecord`, `MutantSpace`, `MetricsSpace`, and `IterationMetrics` with backward-compatible SQLite persistence and schema tolerance for legacy checkpoints.
5. **Interactive UI Integration**: Updated the dashboard mutant table with distinct visual badges (`🟢 KILLED`, `🔵 EQUIV`, `🟡 POTENTIAL`, `🟠 TIMEOUT`, `⚪ INVALID`, `🟣 ERROR`, `🔴 SURVIVED`) and an Equivalence Analysis provenance inspector.
6. **Empirical Benchmarking & 100% Test Pass**: All 293 unit, integration, and security tests pass cleanly; empirical benchmarks across 4 standard workloads demonstrate a 100% valid mutant generation rate and 100% multi-run determinism.

---

## 2. Architecture & Module Responsibilities

The Milestone 2 mutation architecture coordinates 5 specialized components:

```
                      ┌───────────────────────────────────────┐
                      │        Source Code (In-Memory)        │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │         testforge/mutator.py          │
                      │     ASTMutator & MutationTransformer  │
                      │  • 10 Deterministic AST Operators     │
                      │  • AST Compile & Syntax Validation    │
                      │  • Provenance & Expression Capture    │
                      └──────────────────┬────────────────────┘
                                         │
                         Generated Mutant Records (PENDING)
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │        testforge/equivalence.py       │
                      │       EquivalentMutantAnalyzer        │
                      │  • Syntactic Identity Rule            │
                      │  • Dead Code Elimination Rule         │
                      │  • Algebraic Zero-Identity Rule       │
                      │  • Domain Relational Invariant Rule   │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │         testforge/sandbox.py          │
                      │        ParallelSandboxRunner          │
                      │  • Ephemeral Subprocess Isolation     │
                      │  • Multi-Core ProcessPoolExecutor     │
                      │  • Timeout & Infrastructure Guard     │
                      │  • Post-Execution Equivalence Hook    │
                      └──────────────────┬────────────────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │       testforge/orchestrator.py       │
                      │  • Score Calculation (Raw vs. Adj)    │
                      │  • Exclude Equivalent from Critic     │
                      │  • Blackboard & SQLite Checkpointing  │
                      └───────────────────────────────────────┘
```

### Module Breakdown:

| Module | Responsibility in Milestone 2 |
| :--- | :--- |
| `testforge/mutator.py` | AST inspection, deterministic node traversal, fault injection, AST syntax compilation check (`ast.parse`), and expression provenance recording. |
| `testforge/equivalence.py` | Semantic equivalence detection, dead code detection (`DeadCodeVisitor`), algebraic identity detection, domain invariant heuristic classification, and mutation score formulas. |
| `testforge/sandbox.py` | Multi-core parallel sandbox execution, assertion failure discrimination, infinite-loop timeout capture, execution tracking (`is_executed`), and post-execution equivalence refinement. |
| `testforge/state.py` | Pydantic data models for `MutantRecord` and `IterationMetrics` containing equivalence classifications, methods, confidence, and score breakdowns. |
| `testforge/blackboard.py` | Partition state spaces (`MutantSpace`, `MetricsSpace`) storing raw vs. adjusted mutation scores, equivalent counts, and surviving diffs. |
| `testforge/diff_inspector.py` | Deterministic checkpoint comparison identifying `newly_equivalent` and `newly_potentially_equivalent` mutants across pipeline stages. |
| `frontend/app.js` & `index.html` | Real-time UI rendering with equivalence badges, filter toggles, diff inspectors, and checkpoint diff timeline. |

---

## 3. Supported Mutation Operators

TestForge M2 implements 10 deterministic, syntax-preserving AST mutation operators:

| Operator Code | Description | Transformation Example | Rationale & Safety |
| :--- | :--- | :--- | :--- |
| `COMP_OP` | Comparison operator inversion | `x > 10` $\rightarrow$ `x <= 10`, `a == b` $\rightarrow$ `a != b` | Inverts logical boundaries; syntax guaranteed valid. |
| `BOUNDARY_SWAP` | Relational boundary swaps | `x < 100` $\rightarrow$ `x <= 100`, `x >= 50` $\rightarrow$ `x > 50` | Probes strict vs. non-strict off-by-one boundary behavior. |
| `OFF_BY_ONE` | Numeric constant shifts in comparisons | `n > 10` $\rightarrow$ `n > 11` and `n > 9` | Tests edge conditions against numeric threshold offsets. |
| `ARITH_OP` | Arithmetic operator swapping | `a + b` $\rightarrow$ `a - b`, `x * y` $\rightarrow$ `x // y` | Tests mathematical correctness in business logic. |
| `LOGICAL_CONN` | Boolean connective swaps | `a and b` $\rightarrow$ `a or b`, `a or b` $\rightarrow$ `a and b` | Tests compound boolean preconditions and guard clauses. |
| `MATH_FUNC` | Built-in math function flips | `round(x, 2)` $\rightarrow$ `round(x, 1)`, `abs(x)` $\rightarrow$ `x` | Tests numerical precision and magnitude invariants. |
| `COND_INV` | Conditional test inversion | `if x:` $\rightarrow$ `if not (x):` | Tests branch decision coverage. |
| `RETURN_VAL` | Return value mutation | `return True` $\rightarrow$ `return False`, `return x` $\rightarrow$ `return None` | Tests caller handling of falsey or null return values. |
| `CONST_VAL` | Literal value changes | `True` $\rightarrow$ `False`, `0` $\rightarrow$ `1`, `str` $\rightarrow$ `""` | Tests hardcoded constants and default arguments. |
| `EXCEPT_HANDLER` | Safe exception type swaps | `except ValueError:` $\rightarrow$ `except TypeError:` | Safely tests error handling coverage using standard builtins. |

### Excluded Operators & Safety Rationale:
- **Arbitrary Statement Deletion**: Excluded because deleting arbitrary statements frequently produces `UnboundLocalError` or invalid syntax blocks (e.g. empty indented bodies), causing infrastructure errors rather than semantic test failures.
- **Dynamic Name Mangling**: Excluded because mutating variable names produces uninformative `NameError` exceptions that obscure real functional bugs.

---

## 4. Mutation Generation Algorithm & Provenance

1. **Inspection Pass (`target_node_id = 0`)**:
   - Parses the input code into an AST: `tree = ast.parse(source_code)`.
   - Walks the AST using `MutationTransformer` in inspection mode.
   - If `target_lines` is specified, only AST nodes residing on those lines are counted.
   - Counts total mutation sites $N$ deterministically.
2. **Deterministic Mutation Pass (`target_node_id = 1..N`)**:
   - For each target site $i \in [1, N]$, parses a clean AST clone: `tree = ast.parse(source_code)`.
   - Mutates exactly the $i$-th eligible AST node.
   - Records `original_expression` via `ast.unparse(orig_node)` and `mutated_expression` via `ast.unparse(mutated_node)`.
   - Fixes AST line locations with `ast.fix_missing_locations(mutated_tree)`.
3. **Syntax Validation Guard**:
   - Unparses the tree into Python code: `mutated_code = ast.unparse(mutated_tree)`.
   - Compiles and validates syntax via `ast.parse(mutated_code)`.
   - If valid, marks `is_valid_syntax = True`, `status = "PENDING"`.
   - If syntax fails, marks `is_valid_syntax = False`, `status = "INVALID"`.
4. **Early Static Equivalence Pass**:
   - Runs `EquivalentMutantAnalyzer.analyze_mutant(record)`.
   - If proven equivalent statically (e.g. inside dead code), classifies as `EQUIVALENT` before sandbox dispatch.
5. **Non-destructive Isolation**:
   - The original source string and file remain 100% unmodified in memory and on disk.

---

## 5. Equivalent-Mutant Analysis Methodology

A mutant that survives the current test suite is **never automatically labeled equivalent**. Surviving merely means the current tests failed to detect it.

Milestone 2 enforces conservative, explainable static heuristics across 4 distinct equivalence rules:

### Rule 1: Syntactic AST Identity (`SYNTACTIC_IDENTITY`)
- **Condition**: `ast.unparse(ast.parse(original_code)) == ast.unparse(ast.parse(mutated_code))`.
- **Classification**: `EQUIVALENT`
- **Confidence**: `HIGH`
- **Reason**: AST normalization reveals identical semantic representations despite cosmetic whitespace or parenthesization differences.

### Rule 2: Provably Unreachable Dead Code (`DEAD_CODE_MUTATION`)
- **Condition**: The mutation site resides on a line number identified by `DeadCodeVisitor` as provably unreachable:
  - Statements positioned after an unconditional `return`, `raise`, `break`, or `continue` within a block.
  - Statements guarded inside `if False:`, `if 0:`, or `while False:`.
  - Statements inside `else:` blocks of statically `if True:` guards.
- **Classification**: `EQUIVALENT`
- **Confidence**: `HIGH`
- **Reason**: Since the code block can never execute under any inputs, all observable runtime outputs and side effects remain strictly invariant.

### Rule 3: Algebraic Zero-Identity Transforms (`SELF_CANCELING_TRANSFORM`)
- **Condition**: Transformations that preserve arithmetic identity:
  - `x + 0` $\leftrightarrow$ `x - 0`
  - `x * 1` $\leftrightarrow$ `x // 1` (in integer domain contexts)
  - `not not True` $\leftrightarrow$ `True`
- **Classification**: `EQUIVALENT`
- **Confidence**: `HIGH`
- **Reason**: Algebraic identity preserves exact numerical or truth values.

### Rule 4: Domain Relational Invariants (`REDUNDANT_BOUNDARY`)
- **Condition**: Boundary comparisons applied to non-negative domain invariants guaranteed by the Python runtime:
  - `len(items) >= 0` mutated to `len(items) > -1`. Both conditions are tautologically `True` for all Python collections.
  - `len(items) < 0` mutated to `len(items) <= -1`. Both conditions are tautologically `False`.
- **Classification**: `POTENTIALLY_EQUIVALENT`
- **Confidence**: `MEDIUM`
- **Reason**: Relational boundary transformation on a non-negative domain invariant (`len(x) >= 0`); condition remains universally true under standard library semantics.

### Classification Categories & Lifecycles:

| Status | Semantics | Execution | Equivalence |
| :--- | :--- | :---: | :---: |
| `PENDING` | Newly generated, awaiting sandbox evaluation | No | None |
| `KILLED` | Test suite assertion detected and killed mutant | Yes | `NOT_EQUIVALENT` |
| `SURVIVED` | Mutant executed cleanly but current tests did not detect it | Yes | `UNKNOWN` (insufficient evidence) |
| `TIMEOUT` | Subprocess timed out (infinite loop or hang caught) | Yes | `NOT_EQUIVALENT` |
| `ERROR` | Subprocess suffered infrastructure or execution crash | Yes | `NOT_EQUIVALENT` |
| `INVALID` | Mutant failed AST compilation or syntax validation | No | `NOT_EQUIVALENT` |
| `EQUIVALENT` | Semantic equivalence provably verified under static analysis | Optional | `EQUIVALENT` (High confidence) |
| `POTENTIALLY_EQUIVALENT` | Heuristic evidence indicates probable equivalence | Yes | `POTENTIALLY_EQUIVALENT` (Medium) |
| `UNKNOWN` | Surviving mutant with no matching equivalence rule | Yes | `UNKNOWN` (None) |

---

## 6. Mutation Score Correctness & Formulas

Pre-M2 mutation scoring suffered from silent conflation (e.g. timeouts or errors skewing the denominator). TestForge Milestone 2 defines explicit, unbundled metrics:

### 1. Evaluable Pool ($M_{\text{eval}}$):
Only syntactically valid mutants that reached evaluation against the test suite:
$$M_{\text{eval}} = M_{\text{killed}} + M_{\text{survived}} + M_{\text{timeout}} + M_{\text{pot\_equiv}} + M_{\text{equiv}}$$

*Note: Invalid mutants ($M_{\text{invalid}}$) and subprocess execution errors ($M_{\text{error}}$) are strictly excluded from the denominator.*

### 2. Raw Mutation Score ($S_{\text{raw}}$):
Measures the percentage of evaluated mutants detected or resolved:
$$S_{\text{raw}} = \begin{cases} \dfrac{M_{\text{killed}} + M_{\text{timeout}}}{M_{\text{eval}}} \times 100, & \text{if } M_{\text{eval}} > 0 \\ 0.0, & \text{if } M_{\text{eval}} = 0 \end{cases}$$

### 3. Adjusted Mutation Score ($S_{\text{adj}}$):
Excludes verified equivalent mutants from the denominator, reflecting true test efficacy against killable mutants:
$$M_{\text{adj\_denom}} = M_{\text{eval}} - M_{\text{equiv}}$$
$$S_{\text{adj}} = \begin{cases} \dfrac{M_{\text{killed}} + M_{\text{timeout}}}{M_{\text{adj\_denom}}} \times 100, & \text{if } M_{\text{adj\_denom}} > 0 \\ 100.0, & \text{if } M_{\text{adj\_denom}} = 0 \text{ and } M_{\text{eval}} > 0 \\ 0.0, & \text{if } M_{\text{eval}} = 0 \end{cases}$$

*Backward Compatibility*: `primary_score` in metrics payloads maps directly to `raw_mutation_score`, ensuring legacy consumers and API endpoints operate without breaking changes.

---

## 7. Blackboard & Checkpoint Persistence Compatibility

### Data Model Upgrades:
- **`MutantRecord`** (`testforge/state.py`):
  - Added optional fields: `equivalence_status`, `equivalence_method`, `equivalence_reason`, `equivalence_confidence`, `is_executed`, `is_valid_syntax`, `original_expression`, `mutated_expression`.
  - Default values ensure full backward compatibility with older snapshots.
- **`MutantSpace`** (`testforge/blackboard.py`):
  - Added `raw_mutation_score`, `adjusted_mutation_score`, `mutants_equivalent`, `mutants_potentially_equivalent`, `mutants_invalid`, `mutants_timed_out`.
- **`MetricsSpace`** (`testforge/blackboard.py`):
  - Added `raw_mutation_score`, `adjusted_mutation_score`, `equivalent_mutants`, `potentially_equivalent_mutants`.
- **`DeterministicDiffInspector`** (`testforge/diff_inspector.py`):
  - Added `newly_equivalent` and `newly_potentially_equivalent` tracking to `mutant_delta`.

### Legacy Snapshot Compatibility:
When an older SQLite snapshot (created prior to Milestone 2) is restored:
- Missing fields default safely to `0`, `0.0`, `None`, or `True` (`is_valid_syntax`).
- Checkpoint diffs comparing an M1 snapshot to an M2 snapshot handle missing vs. null transitions deterministically without schema errors.

---

## 8. UI Integration

1. **Mutants Audit Table**:
   - Displays real-time status badges:
     - `🟢 KILLED`: Killed by assertion failure.
     - `🔵 EQUIV`: Verified equivalent mutant (excluded from critic).
     - `🟡 POTENTIAL`: Potentially equivalent domain invariant.
     - `🟠 TIMEOUT`: Infinite loop guardrail triggered.
     - `⚪ INVALID`: Syntax compilation error.
     - `🔴 SURVIVED`: Surviving mutant requiring critique.
   - Filter group includes an **Equiv** toggle (`cnt-equiv-mut`).
2. **AST Diff & Equivalence Inspector**:
   - Inspecting any mutant renders the unified diff alongside an **Equivalence Analysis** box displaying the classification method, reason, confidence, original expression, and mutated expression.
3. **Checkpoint Timeline & Diff Modal**:
   - Checkpoint inspection displays `Raw Score / Adj Score` pills and total equivalent mutants count.
   - Checkpoint comparison highlights `🔵 Verified Equivalent` transitions in the mutant state transition card.

---

## 9. Verification & Test Results

### Test Suite Execution:
All 293 tests across 26 test suites passed cleanly in the `.venv-release` environment:

```bash
.venv-release/bin/python -m pytest tests/ -q
# Output:
293 passed, 206 warnings in 311.75s (0:05:11)
```

### Dedicated Milestone 2 Test Suites:
- `tests/test_ast_mutation_m2.py`: **11 passed** in 0.18s
- `tests/test_equivalent_mutants.py`: **9 passed** in 0.06s
- `tests/test_mutation_scores.py`: **7 passed** in 0.05s
- `tests/test_mutation_integration_m2.py`: **5 passed** in 0.07s
- Total targeted M2 suite: **54 passed** in 7.09s

---

## 10. Empirical Benchmark Results

Evaluated 4 standard benchmark workloads across 3 repeated runs on Apple Silicon M2 Pro (10 CPU cores):

| Workload | Mutants Generated | Valid Syntax Rate | Killed | Survived | Equiv | Pot. Eq | Raw Score | Adj Score | Mean Runtime | Deterministic |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **E-Commerce Discount Rules** (`samples/discount.py`) | 19 | 100.0% | 14 | 5 | 0 | 0 | 73.68% | 73.68% | 0.9745s | **True** |
| **Banking Transaction Rules** (`samples/banking.py`) | 23 | 100.0% | 23 | 0 | 0 | 0 | 100.0% | 100.0% | 1.0379s | **True** |
| **Inventory Tier Pricing** (`samples/inventory_pricing.py`) | 37 | 100.0% | 37 | 0 | 0 | 0 | 100.0% | 100.0% | 1.6488s | **True** |
| **Token Bucket Rate Limiter** (`samples/rate_limiter.py`) | 38 | 100.0% | 21 | 17 | 0 | 0 | 55.26% | 55.26% | 1.6006s | **True** |
| **TOTALS / AVERAGES** | **117** | **100.0%** | **95** | **22** | **0** | **0** | **82.24%** | **82.24%** | **1.315s** | **100% Deterministic** |

*Evidence artifacts stored at*: `qa_artifacts/milestone2_ast_mutation_20261023_140500/`

---

## 11. Security & Isolation Considerations

1. **Subprocess Isolation**: Mutants are executed inside ephemeral temporary directories (`tempfile.TemporaryDirectory`) with custom working directories, ensuring mutated files cannot overwrite repository source files.
2. **Timeout Guardrails**: Strict 5-second subprocess timeouts catch infinite loops generated by relational or arithmetic mutations.
3. **AST Firewall**: Pre-execution AST scanning prevents dangerous imports (`os.system`, `subprocess.Popen`) during test synthesis.
4. **Subprocess Caveat**: Subprocess isolation is an operational sandbox against accidental modification and resource exhaustion, not a complete kernel security boundary.

---

## 12. Future Work (Beyond Milestone 2)

- **SMT / Constraint Solver Integration**: Introduce Z3 or PyExZ3 for formal path condition satisfiability to prove equivalence of complex conditional branches.
- **Higher-Order Mutation (HOM)**: Explore combinations of 2 or more subtle mutations to simulate realistic coupling effect bugs.
- **Dynamic Mutant Triage**: Cache test execution profiles to skip re-running tests that do not cover the mutated line.
