# 04 — Benchmark Results: `samples/uploaded_logistics_engine.py`

**Audit Timestamp:** `2026-10-30T18:12:20+05:30`  
**Target Module:** `samples/uploaded_logistics_engine.py`  
**Task ID:** `fix_eval_logistics`  
**Checkpoint Database:** `qa_artifacts/final_defect_fixes_20261030_175000/logistics_benchmark.db`  
**Exported Test Artifact:** `qa_artifacts/final_defect_fixes_20261030_175000/test_hardened_logistics.py`

---

## 1. Execution Summary Metrics

| Metric | Measured Value | Verification Source |
| :--- | :--- | :--- |
| **Target Function** | `calculate_item_discount(unit_price, quantity)` | AST Analysis |
| **Generated Tests** | 3 | Checkpoint DB `SuiteSpace` |
| **Baseline Passing Tests** | 3 / 3 (100.0%) | Sandbox Validation Log |
| **Failed Tests** | 0 | Sandbox Validation Log |
| **Line Coverage** | 26.52% (35 of 132 statements) | `coverage.py` report |
| **Total Valid Mutants** | 258 | AST Mutation Engine |
| **Killed Mutants** | **8** | AST Mutation Engine |
| **Surviving Mutants** | 250 | AST Mutation Engine |
| **Equivalent Mutants** | 0 | AST Mutation Engine |
| **Mutation Score** | **3.10%** | Independent Calculation |
| **Execution Duration** | 16.82s total (12.79s mutation evaluation) | Lifecycle Trace Log |

---

## 2. Independent Mutation Score Recalculation

The formal mutation score formula used by TestForge is:
$$\text{Mutation Score} = \left( \frac{K}{M - E} \right) \times 100$$

Where:
- $K = 8$ (Mutants killed)
- $M = 258$ (Total valid mutants generated and executed)
- $E = 0$ (Identified equivalent mutants)

Recalculating with exact arithmetic:
$$\text{Score} = \left( \frac{8}{258 - 0} \right) \times 100 = \frac{800}{258} \approx 3.100775...\% \rightarrow \mathbf{3.10\%}$$

The database recorded score matches the recalculated score exactly.

---

## 3. Comparison with Historical Live Demo Benchmark

| Metric | Live Demo (`20261030_170700`) | Post-Defect-Fix Benchmark | Improvement Delta |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 160.5s | **16.82s** | **89.5% faster** |
| **Generated Tests** | 11 (generic fallback) | 3 (signature-aware) | Clean, focused suite |
| **Passing Tests** | 11 / 11 | 3 / 3 | 100% clean baseline |
| **Mutants Generated** | 258 | 258 | Identical target scope |
| **Mutants Killed** | **0** | **8** | **+8 mutants killed** |
| **Mutants Survived** | 258 | 250 | -8 survivors |
| **Mutation Score** | **0.00%** | **3.10%** | **+3.10% genuine gain** |
| **Exception Swallowing** | YES (`except Exception: pass`) | **NO (Clean assertions)** | Defect eliminated |

### Key Takeaway
In the live demo, all 11 generated tests contained `except Exception: pass`, which masked runtime failures and resulted in 0 killed mutants (0.0% score) despite 100% test pass rates. In this post-fix benchmark, signature-aware nominal inputs without exception swallowing successfully executed against clean code and genuinely killed 8 AST mutants (3.10% score).

