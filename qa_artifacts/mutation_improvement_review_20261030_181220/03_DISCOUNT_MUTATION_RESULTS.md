# 03 — Benchmark Results: `samples/discount.py`

**Audit Timestamp:** `2026-10-30T18:12:20+05:30`  
**Target Module:** `samples/discount.py`  
**Task ID:** `fix_eval_discount`  
**Checkpoint Database:** `qa_artifacts/final_defect_fixes_20261030_175000/discount_benchmark.db`  
**Exported Test Artifact:** `qa_artifacts/final_defect_fixes_20261030_175000/test_hardened_discount.py`

---

## 1. Execution Summary Metrics

| Metric | Measured Value | Verification Source |
| :--- | :--- | :--- |
| **Target Function** | `calculate_discount(price, quantity, is_member)` | AST Analysis |
| **Generated Tests** | 2 | Checkpoint DB `SuiteSpace` |
| **Baseline Passing Tests** | 2 / 2 (100.0%) | Sandbox Validation Log |
| **Failed Tests** | 0 | Sandbox Validation Log |
| **Line Coverage** | 70.0% (7 of 10 statements) | `coverage.py` report |
| **Total Valid Mutants** | 19 | AST Mutation Engine |
| **Killed Mutants** | 1 | AST Mutation Engine |
| **Surviving Mutants** | 18 | AST Mutation Engine |
| **Equivalent Mutants** | 0 | AST Mutation Engine |
| **Mutation Score** | **5.26%** | Independent Calculation |
| **Execution Duration** | 2.86s total (0.96s mutation evaluation) | Lifecycle Trace Log |

---

## 2. Independent Mutation Score Recalculation

The formal mutation score formula used by TestForge is:
$$\text{Mutation Score} = \left( \frac{K}{M - E} \right) \times 100$$

Where:
- $K = 1$ (Mutants killed)
- $M = 19$ (Total valid mutants generated and executed)
- $E = 0$ (Identified equivalent mutants)

Recalculating with exact arithmetic:
$$\text{Score} = \left( \frac{1}{19 - 0} \right) \times 100 = \frac{100}{19} \approx 5.26315789...\% \rightarrow \mathbf{5.26\%}$$

The database recorded score matches the recalculated score exactly.

---

## 3. Comparison Between Initial Suite and Refined Suite

- **Pre-Fix Suite (Defect 3 Active):**
  - Synthesized `calculate_discount(2, 3)` (only 2 arguments provided for a 3-argument function).
  - Failed baseline check with `TypeError: calculate_discount() missing 1 required positional argument: 'is_member'`.
  - Fallback generated generic try/except test swallowing the error, leaving coverage incomplete.
- **Post-Fix Refined Suite:**
  - Synthesized `calculate_discount(10.0, 2, False)` matching the complete signature.
  - Passed baseline check on pass@1 cleanly without errors or fallbacks.
  - Achieved 70% line coverage and killed 1 mutant (boundary/relational mutation) on nominal execution.

