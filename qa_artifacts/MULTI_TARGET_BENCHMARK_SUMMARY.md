# TestForge Multi-Target Empirical Benchmark Evaluation Matrix
- **Single Source of Truth:** `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`
- **Evaluation Timestamp:** 2026-11-07T17:40:00
- **Repetitions per Target:** 3 (mean across 3 seeds)
- **Target Count:** 4 diverse real-world Python modules
- **Provenance Rule:** Dual-reporting enforced: Pipeline-Only vs Pipeline + Manual Oracles.

## 1. Target Modules Characterization & Mutation Space

| Module | Path | LOC | Discovered Callables | Injected Mutants | Operator Categories |
|---|---|---|---|---|---|
| **discount.py** | `samples/discount.py` | 19 | 1 | 19 | `BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, LOGICAL_CONN, MATH_FUNC, RETURN_VAL` |
| **order_fsm.py** | `samples/order_fsm.py` | 85 | 6 | 106 | `BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, LOGICAL_CONN, OFF_BY_ONE, RETURN_VAL` |
| **lru_cache.py** | `samples/lru_cache.py` | 65 | 5 | 42 | `BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, LOGICAL_CONN, RETURN_VAL` |
| **stats_calculator.py** | `samples/stats_calculator.py` | 65 | 6 | 73 | `ARITH_OP, BOUNDARY_SWAP, COMP_OP, COND_INV, CONST_VAL, MATH_FUNC, OFF_BY_ONE, RETURN_VAL` |

## 2. Multi-Scenario Empirical Performance Scorecard

| Target Module | Scenario | Line Cov (%) | Branch Cov (%) | Raw MS (%) | Adj MS (%) | Killed / Total (Equiv) | Latency (s) | Tokens | Status |
|---|---|---|---|---|---|---|---|---|---|
| discount.py | **baseline** | 50.0% | 50.0% | 5.3% | 5.6% | 1 / 19 (eq: 1) | 0.05s | 0 | COMPLETED (n=3) |
| discount.py | **zeroshot** | 50.0% | 50.0% | 63.2% | 66.7% | 12 / 19 (eq: 1) | 1.25s | 450 | COMPLETED (n=3) |
| discount.py | **agentic_reflection** | 50.0% | 50.0% | 89.5% | 94.4% | 17 / 19 (eq: 1) | 2.45s | 1,250 | COMPLETED (n=3) |
| discount.py | **pipeline_plus_manual** | 100.0% | 100.0% | 94.7% | 100.0% | 18 / 19 (eq: 1) | 2.45s | 1,250 | COMPLETED (n=3) |
| order_fsm.py | **baseline** | 20.0% | 15.0% | 6.6% | 6.7% | 7 / 106 (eq: 1) | 0.08s | 0 | COMPLETED (n=3) |
| order_fsm.py | **zeroshot** | 36.7% | 21.9% | 13.2% | 13.3% | 14 / 106 (eq: 1) | 2.10s | 820 | COMPLETED (n=3) |
| order_fsm.py | **agentic_reflection** | 36.7% | 21.9% | 13.2% | 13.3% | 14 / 106 (eq: 1) | 36.50s | 4,200 | COMPLETED (n=3) |
| order_fsm.py | **pipeline_plus_manual** | 78.9% | 68.8% | 69.8% | 70.5% | 74 / 106 (eq: 1) | 36.50s | 4,200 | COMPLETED (n=3) |
| lru_cache.py | **baseline** | 25.0% | 12.5% | 7.1% | 7.9% | 3 / 42 (eq: 4) | 0.05s | 0 | COMPLETED (n=3) |
| lru_cache.py | **zeroshot** | 30.0% | 15.0% | 23.8% | 26.3% | 10 / 42 (eq: 4) | 1.45s | 620 | COMPLETED (n=3) |
| lru_cache.py | **agentic_reflection** | 34.7% | 18.8% | 30.9% | 34.2% | 13 / 42 (eq: 4) | 8.20s | 2,100 | COMPLETED (n=3) |
| lru_cache.py | **pipeline_plus_manual** | 34.7% | 18.8% | 30.9% | 34.2% | 13 / 42 (eq: 4) | 8.20s | 2,100 | COMPLETED (n=3) |
| stats_calculator.py | **baseline** | 28.0% | 25.0% | 6.8% | 7.0% | 5 / 73 (eq: 2) | 0.06s | 0 | COMPLETED (n=3) |
| stats_calculator.py | **zeroshot** | 40.0% | 35.0% | 30.1% | 31.0% | 22 / 73 (eq: 2) | 1.85s | 770 | COMPLETED (n=3) |
| stats_calculator.py | **agentic_reflection** | 47.6% | 43.8% | 45.2% | 46.5% | 33 / 73 (eq: 2) | 12.40s | 3,100 | COMPLETED (n=3) |
| stats_calculator.py | **pipeline_plus_manual** | 47.6% | 43.8% | 45.2% | 46.5% | 33 / 73 (eq: 2) | 12.40s | 3,100 | COMPLETED (n=3) |

## 3. Cross-Target Statistical Aggregation (Single Source of Truth)

| Metric | Baseline | Zero-Shot | Pipeline-Only Reflection | Pipeline + Manual Oracles | Pipeline-Only vs Baseline | Pipeline-Only vs Zero-Shot |
|---|---|---|---|---|---|---|
| **Arithmetic Mean Line Coverage** | 30.8% | 39.2% | 42.2% | 65.3% | **+11.5%** | **+3.1%** |
| **Arithmetic Mean Branch Coverage** | 25.6% | 30.5% | 33.6% | 57.9% | **+8.0%** | **+3.1%** |
| **Geometric Mean Branch Coverage** | 22.0% | 27.5% | 30.8% | 48.8% | — | — |
| **Arithmetic Mean Raw Mutation Score** | 6.5% | 32.6% | 44.7% | 60.2% | **+38.2%** | **+12.1%** |
| **Geometric Mean Raw Mutation Score** | 6.4% | 27.8% | 35.9% | 55.2% | — | — |
| **Arithmetic Mean Adjusted Mutation Score** | 6.8% | 34.3% | 47.1% | 62.8% | **+40.3%** | **+12.8%** |
| **Geometric Mean Adjusted Mutation Score** | 6.7% | 29.2% | 37.6% | 57.9% | — | — |
| **Mean Latency (sec)** | 0.06s | 1.66s | 14.89s | 14.89s | — | — |

> [!IMPORTANT]
> - **Provenance Verification:** All figures derive directly from `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`.
> - **Pipeline-Only:** Fully autonomous AST generation and reflection repair without human-written test cases.
> - **Pipeline + Manual:** Combined scores incorporating human-authored precision and FSM transition oracles from `tests/manual_oracles/`.
