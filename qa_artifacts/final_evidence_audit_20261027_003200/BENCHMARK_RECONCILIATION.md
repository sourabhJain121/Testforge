# TestForge — Benchmark Reconciliation & Source of Truth Audit

**Audit Date:** 2026-10-27  
**Artifact Directory:** `qa_artifacts/final_evidence_audit_20261027_003200/`  
**Primary Source of Truth:** `qa_artifacts/phase2_finalization_20261026_141500/phase5_m2_quality/raw_benchmark_results.json`  
**Secondary Raw Record:** `qa_artifacts/phase2_finalization_20261026_141500/phase5_m2_quality/strategy_comparison.csv`  
**Auditor:** Independent Evidence & Quality Auditor  

---

## 1. Executive Summary of Benchmark Audit

An exhaustive automated recomputation of all benchmark metrics was executed against the primary machine output: `raw_benchmark_results.json`. The audit established:

1. **Defensible Empirical Metrics:**
   - **Remediated Agentic Reflection:** Mean Mutation Score of **71.28%** (arithmetic mean across 5 fixtures) or **69.65%** (pooled across all 201 evaluated mutants), with an **80.00%** defect detection rate, **0.00%** false-positive rate, and **18.22s** mean runtime.
   - **Zero-Shot:** Mean Mutation Score of **45.32%** (arithmetic) or **43.28%** (pooled), with a **26.66%** defect detection rate, **0.00%** false-positive rate, and **2.96s** mean runtime.
   - **Handwritten Baseline:** Mean Mutation Score of **76.62%** (arithmetic) or **76.12%** (pooled), with a **100.00%** defect detection rate, **0.00%** false-positive rate, and **3.10s** mean runtime.
   - **Relative Delta:** Agentic Reflection decisively outperforms Zero-Shot by **+25.96%** (arithmetic mutation score) and **+53.34%** (defect detection rate).

2. **Resolution of Markdown Table Discrepancies:**
   - In `phase5_m2_quality/BENCHMARK_COMPARISON.md`, the aggregate summary table (Section 1) perfectly matches the machine-recorded arithmetic means.
   - However, the per-fixture breakdown table (Section 2) contains copy-paste discrepancies in fixture names and mutant counts for three fixtures:
     - It labeled fixtures as `inventory_allocator` (43 mutants) and `banking_ledger` (37 mutants), whereas the underlying code evaluated `inventory_pricing_calculator` (37 mutants) and `banking_operations_module` (23 mutants).
     - It listed `token_bucket_limiter` as 19 kills (zeroshot) and 27 kills (agentic), whereas the raw JSON records 16 kills (zeroshot, 42.1%) and 26 kills (agentic, 68.4%).
   - **Verdict:** `raw_benchmark_results.json` and `strategy_comparison.csv` represent the authentic recorded execution. This report establishes the reconciled per-fixture table directly from the raw records.

3. **Execution Mode & Repetition Transparency:**
   - The reported benchmark consists of **5 distinct reference fixtures evaluated over 1 trial each (`repetitions: 1`)**. It should NOT be described as a multi-run trial over independent repetitions.
   - The execution mode was **`OFFLINE_DETERMINISTIC_SYNTHESIS`** (for zeroshot and agentic) and **`DETERMINISTIC_BASELINE`** (for handwritten), consuming **0 live LLM tokens** ($0.00 spend). It validates the deterministic rule generator, clean-reference validator, suite merger, and mutant execution pipeline, rather than stochastic live LLM sampling.

---

## 2. Reconciled Per-Fixture Source of Truth

The table below reflects the exact data stored in `raw_benchmark_results.json` and `strategy_comparison.csv`:

| Fixture ID | Fixture Description | Strategy | Tests Retained | Clean Ref Passed | Mutants Total | Mutants Killed | Mutation Score (%) | Defect Detection (%) | FP Rate (%) | Runtime (s) | Execution Mode |
|---|---|---|---:|:---:|---:|---:|---:|---:|---:|---:|---|
| `task_state_transition` | Task & Order State Machine | Baseline | 9 | PASS | 57 | 41 | 71.90% | 100.00% | 0.00% | 4.08s | `DETERMINISTIC_BASELINE` |
| `task_state_transition` | Task & Order State Machine | Zero-Shot | 1 | PASS | 57 | 12 | 21.10% | 0.00% | 0.00% | 3.58s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `task_state_transition` | Task & Order State Machine | **Agentic Reflection** | 2 | PASS | 57 | 33 | **57.90%** | **33.30%** | 0.00% | 12.99s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `token_bucket_rate_limiter`| Token Bucket Limiter | Baseline | 8 | PASS | 38 | 31 | 81.60% | 100.00% | 0.00% | 3.01s | `DETERMINISTIC_BASELINE` |
| `token_bucket_rate_limiter`| Token Bucket Limiter | Zero-Shot | 1 | PASS | 38 | 16 | 42.10% | 33.30% | 0.00% | 2.92s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `token_bucket_rate_limiter`| Token Bucket Limiter | **Agentic Reflection** | 2 | PASS | 38 | 26 | **68.40%** | **66.70%** | 0.00% | 18.22s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `inventory_pricing_calculator`| Inventory Tier Pricing | Baseline | 9 | PASS | 37 | 27 | 73.00% | 100.00% | 0.00% | 2.87s | `DETERMINISTIC_BASELINE` |
| `inventory_pricing_calculator`| Inventory Tier Pricing | Zero-Shot | 1 | PASS | 37 | 17 | 46.00% | 0.00% | 0.00% | 2.90s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `inventory_pricing_calculator`| Inventory Tier Pricing | **Agentic Reflection** | 2 | PASS | 37 | 28 | **75.70%** | **100.00%** | 0.00% | 20.90s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `banking_operations_module`| Banking Operations | Baseline | 8 | PASS | 23 | 18 | 78.30% | 100.00% | 0.00% | 2.38s | `DETERMINISTIC_BASELINE` |
| `banking_operations_module`| Banking Operations | Zero-Shot | 1 | PASS | 23 | 12 | 52.20% | 33.30% | 0.00% | 2.31s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `banking_operations_module`| Banking Operations | **Agentic Reflection** | 2 | PASS | 23 | 18 | **78.30%** | **100.00%** | 0.00% | 26.45s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `currency_converter` | Currency Converter | Baseline | 8 | PASS | 46 | 36 | 78.30% | 100.00% | 0.00% | 3.18s | `DETERMINISTIC_BASELINE` |
| `currency_converter` | Currency Converter | Zero-Shot | 1 | PASS | 46 | 30 | 65.20% | 66.70% | 0.00% | 3.09s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| `currency_converter` | Currency Converter | **Agentic Reflection** | 2 | PASS | 46 | 35 | **76.10%** | **100.00%** | 0.00% | 12.55s | `OFFLINE_DETERMINISTIC_SYNTHESIS` |

---

## 3. Arithmetic Mean vs. Pooled Aggregate Metrics

Evaluators should explicitly distinguish between the **unweighted arithmetic mean of per-fixture scores** and the **pooled score across all mutants**:

| Strategy | Arithmetic Mean Mutation Score | Pooled Mutation Score (Killed / Total) | Arithmetic Mean Defect Detection | Pooled Defect Detection (Detected / Total) | Mean Line Coverage | Mean FP Rate | Mean Runtime | Total Spend |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Handwritten Baseline** | 76.62% | 76.12% (153 / 201) | 100.00% | 100.00% (15 / 15) | 100.00% | 0.00% | 3.10 s | $0.00 |
| **Zero-Shot** | 45.32% | 43.28% (87 / 201) | 26.66% | 26.67% (4 / 15) | 79.30% | 0.00% | 2.96 s | $0.00 |
| **Remediated Agentic Reflection** | **71.28%** | **69.65% (140 / 201)** | **80.00%** | **80.00% (12 / 15)** | **98.58%** | **0.00%** | **18.22 s** | **$0.00** |
| **Agentic Advantage vs. Zero-Shot** | **+25.96%** | **+26.37%** | **+53.34%** | **+53.33%** | **+19.28%** | **0.00%** | +15.26 s | $0.00 |

### Mathematical Formulae
1. **Arithmetic Mean Mutation Score:**
   $$\text{Mean Score} = \frac{1}{N} \sum_{i=1}^{N} \text{Score}_i$$
   - Agentic: $(57.90 + 68.40 + 75.70 + 78.30 + 76.10) / 5 = 356.40 / 5 = \mathbf{71.28\%}$
   - Zero-Shot: $(21.10 + 42.10 + 46.00 + 52.20 + 65.20) / 5 = 226.60 / 5 = \mathbf{45.32\%}$
   - Baseline: $(71.90 + 81.60 + 73.00 + 78.30 + 78.30) / 5 = 383.10 / 5 = \mathbf{76.62\%}$

2. **Pooled Mutation Score:**
   $$\text{Pooled Score} = \frac{\sum_{i=1}^{N} \text{Killed}_i}{\sum_{i=1}^{N} \text{Mutants}_i} \times 100$$
   - Agentic: $(33 + 26 + 28 + 18 + 35) / (57 + 38 + 37 + 23 + 46) = 140 / 201 = \mathbf{69.65\%}$
   - Zero-Shot: $(12 + 16 + 17 + 12 + 30) / 201 = 87 / 201 = \mathbf{43.28\%}$
   - Baseline: $(41 + 31 + 27 + 18 + 36) / 201 = 153 / 201 = \mathbf{76.12\%}$

3. **Defect Detection Rate:**
   - Both arithmetic mean and pooled defect detection yield **80.00%** for Agentic Reflection (12 of 15 ground-truth defects detected across 5 fixtures) versus **26.66%** for Zero-Shot (4 of 15 detected).

---

## 4. Key Invariants & Sanity Checks Verified

- **Clean-Reference Invariant:** Every candidate test suite passed clean reference code (`tests_failed_on_reference = 0`, `false_positive_rate_pct = 0.0%`).
- **Defect Evaluation:** Every defect was independently tested against the buggy variant code.
- **Suite Preservation:** For `currency_converter`, Pass 0 tests were preserved and merged with Pass 1, yielding 2 valid tests that kill 35 mutants (76.10%) and detect 100% of defects.
- **Denominators:** Mutants total is consistently 201 across all three strategies.
- **Audit Verification Script:** Verified by executing `benchmark_recompute.py` (exit code 0).
