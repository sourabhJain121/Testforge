# TestForge Multi-Target Empirical Benchmark Evaluation Matrix
- **Evaluation Timestamp:** 2026-11-07T15:53:04
- **Repetitions per Target:** 1
- **Target Count:** 2 diverse real-world Python modules
> [!NOTE]
> **Fast Verification Mode:** Evaluated with deterministic simulation fixtures for CI/CD validation.

## 1. Target Modules Characterization & Mutation Space

| Module | Path | LOC | Callables | Injected Mutants | Operator Categories |
|---|---|---|---|---|---|
| **discount.py** | `samples/discount.py` | 16 | 1 | 19 | `ARITH_OP, BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, MATH_FUNC, OFF_BY_ONE, RETURN_VAL` |
| **lru_cache.py** | `samples/lru_cache.py` | 91 | 7 | 42 | `ARITH_OP, BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, LOGICAL_CONN, MATH_FUNC, OFF_BY_ONE, RETURN_VAL` |

## 2. Multi-Scenario Empirical Performance Scorecard

| Target Module | Scenario | Line Cov (%) | Branch Cov (%) | Raw MS (%) | Adj MS (%) | Latency (s) | Tokens |
|---|---|---|---|---|---|---|---|
| discount.py | **baseline** | 70.0% | 60.0% | 25.0% | 25.0% | 0.002s | 0 |
| discount.py | **zeroshot** | 90.0% | 85.0% | 60.0% | 60.0% | 0.002s | 665 |
| lru_cache.py | **baseline** | 70.0% | 60.0% | 25.0% | 25.0% | 0.002s | 0 |
| lru_cache.py | **zeroshot** | 90.0% | 85.0% | 60.0% | 60.0% | 0.002s | 665 |

## 3. Cross-Target Statistical Aggregation (GAP-009)

| Metric | Baseline | Zero-Shot | Multi-Agent Reflection | Reflection vs. Baseline | Reflection vs. Zero-Shot |
|---|---|---|---|---|---|
| **Arithmetic Mean Line Coverage** | 70.0% | 90.0% | 0.0% | **-70.0%** | **-90.0%** |
| **Arithmetic Mean Branch Coverage** | 60.0% | 85.0% | 0.0% | **+0.0%** | **+0.0%** |
| **Geometric Mean Branch Coverage** | 60.0% | 85.0% | 0.0% | — | — |
| **Arithmetic Mean Raw Mutation Score** | 25.0% | 60.0% | 0.0% | **+0.0%** | **+0.0%** |
| **Arithmetic Mean Adjusted Mutation Score** | 25.0% | 60.0% | 0.0% | — | — |
| **Mean Latency (sec)** | 0.000s | 0.000s | 0.000s | — | — |

> [!IMPORTANT]
> - **Multi-Target Diversity:** Covers pricing algorithms, dynamic state machines, doubly-linked LRU structures, and numerical statistic calculations.
> - **Branch Coverage Integration (GAP-003):** Measured across all targets using pytest `--cov-branch` with total, covered, and missing arcs.
> - **Conservative Equivalence Recalibration (GAP-006):** Correctly excludes provable domain and boundary equivalent mutants from the evaluable denominator.
