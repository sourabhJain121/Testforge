# TestForge Agentic Regression Diagnosis & Never-Regress Guard Specification

**Document Version:** 1.0.0  
**Status:** FROZEN DIAGNOSIS & REMEDIATION SPECIFICATION  
**Author:** Principal Evaluation & Systems Lead  
**Scope:** Sealed V2 Evaluation (`samples/sealed_v2/`) & Orchestrator Hardening Loop  

---

## 1. Executive Summary

During the frozen Sealed V2 evaluation across 6 real-world Python standard library algorithmic modules (`bisect_algo`, `fractions_algo`, `heapq_algo`, `shlex_algo`, `statistics_algo`, `textwrap_algo`), an empirical regression was detected between **TestForge Deterministic** (AST synthesis) and **TestForge Full Agentic** (multi-agent reflection loop):

| Sealed V2 Target | Developer Baseline | TestForge Deterministic | TestForge Full Agentic | Delta (Full vs Det) | Root Failure Mode |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `bisect_algo` | 0.0% | **100.0%** (70/70) | **0.0%** (0/70) | **-100.0%** | Sequence parameter `TypeError` → Pass@1 failure → 0 mutants |
| `heapq_algo` | 36.7% | **100.0%** (30/30) | **0.0%** (0/30) | **-100.0%** | Sequence parameter `TypeError` → Pass@1 failure → 0 mutants |
| `fractions_algo` | 0.0% | 21.8% | 21.8% | ±0.0% | Exact match across all seeds |
| `shlex_algo` | 0.0% | 60.9% | 60.9% | ±0.0% | Exact match across all seeds |
| `statistics_algo` | 0.0% | 59.5% | 59.5% | ±0.0% | Exact match across all seeds |
| `textwrap_algo` | 0.0% | 39.1% | 39.1% | ±0.0% | Exact match across all seeds |

In 4 out of 6 targets, deterministic AST synthesis and full agentic reflection achieved identical scores. In the remaining 2 targets (`bisect_algo` and `heapq_algo`), deterministic synthesis achieved 100% mutation score while full agentic reflection collapsed to 0.0%.

This document diagnoses the exact failure mechanisms and specifies the **Never-Regress Guard** implemented in `testforge/orchestrator.py`.

---

## 2. Root Cause Analysis

### Root Cause 1: Orchestrator History-Last Finalization Defect
In `testforge/orchestrator.py` (lines 417, 1968–1972):
```python
self.state.final_mutation_score = self.state.history[-1].mutation_score if self.state.history else 0.0
raw_final = self.state.history[-1].raw_mutation_score if self.state.history else 0.0
adj_final = self.state.history[-1].adjusted_mutation_score if self.state.history else 0.0
```
The orchestrator unconditionally reported the metrics of `self.state.history[-1]`—the **final iteration executed**—rather than the **optimal suite discovered across all iterations**. If an agentic reflection cycle (or code synthesis pass) produced a degraded suite in Iteration $k+1$ after a high-scoring Iteration $k$, the degraded suite replaced the optimal suite in `self.state.current_test_code` and was published as the final outcome.

### Root Cause 2: Sequence-Typed Parameter Heuristic Limitation (`bisect_algo` 0/70)
In `samples/sealed_v2/bisect_algo.py`:
```python
def insort_right(a, x, lo=0, hi=None, *, key=None):
    if key is None:
        lo = bisect_right(a, x, lo, hi)
    else:
        lo = bisect_right(a, key(x), lo, hi, key=key)
    a.insert(lo, x)
```
Standard library algorithms frequently omit Python type annotations on positional parameters. The function parameter `a` represents a sequence (list), and `x` represents an item.
In `testforge/agents.py:build_nominal_arguments()`:
```python
p_low = p.lower()
if t in ("list", "sequence"):
    pos_vals.append("[]")
elif any(x in p_low for x in ("price", "amount", ...)):
    pos_vals.append("10.0")
...
else:
    pos_vals.append("1")  # Default integer fallback
```
When inspecting `insort_right(a, x)`:
- `p = "a"` has no type annotation (`t = ""`) and matches no keyword heuristics (`p_low != "items"`).
- The argument builder defaulted to scalar integer `1`.
- The synthesized test invoked: `insort_right(1, 1)`.
- Inside `bisect_algo.py`, `hi = len(a)` immediately threw:
  `TypeError: object of type 'int' has no len()`

### Root Cause 3: Clean Target Pass@1 Safety Invariant
Under TestForge's verification invariants:
1. Every candidate test suite must pass 100% cleanly against un-mutated target source code (`pass@1`).
2. If tests fail against clean code, `self.state.baseline_passed` is set to `False`.
3. To prevent false mutant kills (where broken tests cause tests to fail regardless of mutant injection), `TestExecutionAgent.evaluate_mutants` aborts evaluation when `baseline_passed is False`.
4. Result: 0 mutants killed out of 70, yielding 0.0% Mutation Score.

### Why Did `testforge_deterministic` Achieve 100% on the Same Targets?
`testforge_deterministic` utilizes `IntelligentASTSynthesizer` (`testforge/intelligent_generator.py`). Unlike naive single-call nominal runners, `IntelligentASTSynthesizer` systematically synthesizes boundary and exception test cases:
```python
def test_insort_right_extreme_a_zero_raises_TypeError():
    with pytest.raises(TypeError):
        insort_right(0, 1, 1, 1, key=None)
```
Because `insort_right(0, 1)` **does** raise `TypeError` on clean code, this test passed against clean code! Then, when mutated code altered boundary comparisons, exception paths, or control flow, those mutations were detected and killed, achieving 100% mutation score.

---

## 3. The Never-Regress Guard

To eliminate agentic regressions and enforce monotonicity across the hardening pipeline, TestForge introduces the **Never-Regress Guard** in `testforge/orchestrator.py`.

### Architectural Specification
1. **Continuous Peak Tracking**:
   At every iteration $i \in [1, \text{max\_iterations}]$, the orchestrator records:
   - `_best_raw_mutation_score: float`
   - `_best_adjusted_mutation_score: float`
   - `_best_test_code: str`
   - `_best_iteration: int`
   - `_best_mutants_killed: int`
   - `_best_mutants: List[Any]`
   - `_best_surviving_diffs: List[str]`

2. **Rollback Trigger**:
   At workflow completion, early exit, timeout, or cancellation:
   $$\text{If } \text{score}(\text{suite}_{\text{last}}) < \text{score}(\text{suite}_{\text{best}}):$$
   - The orchestrator automatically triggers a rollback to $\text{suite}_{\text{best}}$.
   - `self.state.current_test_code` is restored to `_best_test_code`.
   - `self.state.final_mutation_score` is restored to `_best_raw_mutation_score`.
   - `self.state.mutants_killed` and `self.state.mutants` are restored to the peak iteration state.
   - Event `NEVER_REGRESS_GUARD_TRIGGERED` is emitted to the audit log.
   - The Blackboard `SuiteSpace` and `MetricsSpace` are synchronized with the optimal state.

3. **Evaluation Protocol Isolation**:
   - **Sealed V2 Protocol Freeze**: Sealed V2 evaluation data in `qa_artifacts/SEALED_V2_RESULTS.json` is **frozen as empirical evidence of pre-fix performance**. It is NOT re-run after this fix, preserving historical scientific integrity.
   - **Verification Scope**: The Never-Regress Guard is verified exclusively on development targets (`samples/discount.py`, `samples/order_fsm.py`) using dedicated regression unit tests in `tests/test_never_regress_guard.py`.

---

## 4. Documented Limitation: Sequence-Typed Parameters

### Limitation Description
In dynamically typed Python programs lacking PEP 484 type annotations, functions accepting untyped container arguments (e.g., `def fn(a, x):` where `a` is expected to be a `list`, `set`, or `tuple`) cannot be reliably exercised by scalar heuristic synthesis without static AST container inference or semantic LLM type deduction.

### Impact
- In pure scalar heuristic synthesis without LLM assistance, passing scalar integers to sequence operations (`len()`, `.insert()`, `[0]`) causes clean-code `TypeError`.
- When LLM generation is unavailable or fails pass@1, fallback synthesis requires either:
  1. AST inspection of internal attribute accesses (e.g., `.insert()`, `.append()`, `len()`) to infer container types.
  2. Or explicit type annotations in target code.
