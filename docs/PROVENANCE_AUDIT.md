# TestForge Mutation Score Provenance & Audit Report

**Date**: November 7, 2026  
**Auditor**: Senior Evaluation Scientist & QA Lead  
**Scope**: 4 Canonical Benchmark Targets (`discount.py`, `order_fsm.py`, `lru_cache.py`, `stats_calculator.py`)  

---

## 1. Executive Findings: Pipeline-Only vs. Manual Oracles

During the Phase 2 audit of benchmark artifacts, an investigation into test provenance revealed that the test suites stored in `qa_artifacts/` for two targets contained hand-authored unit tests:
1. `qa_artifacts/test_hardened_discount.py` had a manual precision test (`test_calculate_discount_two_decimal_precision`) appended during surviving mutant analysis, killing `MUT_MATH_FUNC_018`.
2. `qa_artifacts/test_hardened_order_fsm.py` had 68 lines of human-written lifecycle transition tests (lines 181–248) appended, which exercised deep FSM states (`SHIPPED`, `DELIVERED`, `RETURNED`, `REFUNDED`, `CANCELLED`) and killed 60 mutants.

### Strict Provenance Policy Enforcement
To maintain academic integrity:
* All hand-authored tests have been extracted from `qa_artifacts/` and isolated in [`tests/manual_oracles/`](file:///Users/sourabh/TestForge/tests/manual_oracles/).
* `qa_artifacts/test_hardened_*.py` files now contain **100% autonomous pipeline-generated code**.
* Dual-reporting is established: **Pipeline-Only** vs. **Pipeline + Manual Oracles**.

---

## 2. Provenance Scorecard Across All 4 Targets

| Target Module | Injected Mutants | Equiv Mutants | Pipeline-Only Killed | Pipeline-Only Raw MS | Pipeline-Only Adj MS | Manual Oracles Available | Pipeline + Manual Killed | Pipeline + Manual Adj MS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`samples/discount.py`** | 19 | 1 | **17** | **89.5%** | **94.4%** | 1 test (`MUT_MATH_FUNC_018`) | **18** | **100.0%** |
| **`samples/order_fsm.py`** | 106 | 1 | **14** | **13.2%** | **13.3%** | 10 tests (Lifecycle transitions) | **74** | **70.5%** |
| **`samples/lru_cache.py`** | 42 | 4 | **13** | **31.0%** | **34.2%** | None (Fully autonomous) | **13** | **34.2%** |
| **`samples/stats_calculator.py`** | 73 | 2 | **33** | **45.2%** | **46.5%** | None (Fully autonomous) | **33** | **46.5%** |

### Cross-Target Means:
* **Pipeline-Only (Autonomous AST Synthesis + Reflection)**:
  * Arithmetic Mean Adj Mutation Score: **47.1%**
  * Geometric Mean Adj Mutation Score: **39.4%**
* **Pipeline + Manual Oracles (Autonomous + Human Expert Oracles)**:
  * Arithmetic Mean Adj Mutation Score: **62.8%**
  * Geometric Mean Adj Mutation Score: **58.6%**

---

## 3. Detailed Per-Target Analysis

### 1. `samples/discount.py`
* **Autonomous Pipeline Generation**: Generates 21 tests covering boundary values ($0.0$, $-0.1$, $0.1$, quantity 4, 5, 6) and booleans (`is_member`).
* **Autonomous Kills**: Kills 17 of 19 mutants.
* **Equivalent Mutant**: `MUT_BOUNDARY_SWAP_003` (`price <= 0.0` vs `price < 0.0`) is mathematically equivalent because $0.0 \times (1 - d) = 0.0$.
* **Survivor**: `MUT_MATH_FUNC_018` (`round(price, 2)` -> `round(price, 1)`).
* **Manual Oracle**: `tests/manual_oracles/test_manual_discount.py` tests `calculate_discount(10.55, 1, False) == 10.55`, killing `MUT_MATH_FUNC_018` to achieve 100.0% adjusted score.

### 2. `samples/order_fsm.py`
* **Autonomous Pipeline Generation**: `IntelligentASTSynthesizer` generates 40 unit tests targeting `validate_transition` and `transition_order_state` with default argument probing.
* **Autonomous Kills**: Kills 14 of 106 mutants (13.3% adj score).
* **Why the Autonomous Loop Missed Deep Mutants**: The autonomous loop probes functions with single nominal inputs and boundary values. However, `OrderFSM` requires multi-step stateful sequential transitions (`CREATED` -> `PENDING_PAYMENT` -> `PAID` -> `PROCESSING` -> `SHIPPED` -> `DELIVERED` -> `COMPLETED`). Without synthesizing sequential method call sequences, later states were never reached.
* **Manual Oracle**: `tests/manual_oracles/test_manual_order_fsm.py` provides 10 sequential transition test methods, killing 60 additional mutants to achieve 74/106 kills (70.5% adj score).
* **Remediation Task for Stage 0.3**: Upgrade the autonomous reflection repair loop (ToT/ReAct) to synthesize multi-step sequential state transitions autonomously.

### 3. `samples/lru_cache.py`
* **Autonomous Pipeline Generation**: Generates tests for `get`, `put`, `evict`.
* **Autonomous Kills**: Kills 13 of 42 mutants (34.2% adj score).
* **Equivalent Mutants**: 4 equivalent mutants identified in internal node pointer updates and capacity checks.
* **Manual Oracles**: None. 100% autonomous.

### 4. `samples/stats_calculator.py`
* **Autonomous Pipeline Generation**: Generates 27 tests covering mathematical operations, single-element collections, and division-by-zero guards.
* **Autonomous Kills**: Kills 33 of 73 mutants (46.5% adj score).
* **Equivalent Mutants**: 2 equivalent mutants.
* **Manual Oracles**: None. 100% autonomous.
