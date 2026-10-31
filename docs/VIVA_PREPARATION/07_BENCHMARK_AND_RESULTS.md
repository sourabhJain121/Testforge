# TestForge: Empirical Benchmarks & Metric Reconciliation

**Document Purpose:** Definitive reference for all empirical benchmark results across Phase 1, Phase 2, Phase 3, and Phase 4, including the complete reconciliation of the UI 94.7% metric.  
**Audited Datasets:** `samples/discount.py` and `samples/uploaded_logistics_engine.py`.  

---

## 1. Evolution of TestForge Benchmarks (Phase 1 to Phase 4)

TestForge's test-generation and mutation-killing capabilities evolved across four verifiable project phases:

```
Phase 1: AST Regression Fix & Baseline Establishment
  • discount.py: 5.26% mutation score (1/19 killed)
  • logistics: 3.10% mutation score (8/258 killed)
  • Defect: Generic assertions ('assert res is not None') & only 1 callable tested.
       │
       ▼
Phase 2: Intelligent Multi-Callable & Boundary Synthesis
  • discount.py: 89.47% mutation score (17/19 killed)
  • logistics: 68.22% mutation score (176/258 killed)
  • Improvement: All 10 callables tested; exact value assertions; BVA applied.
       │
       ▼
Phase 3: Independent Reproduction & Cryptographic Validation
  • 100% blind reproduction of Phase 2 metrics with zero variance.
  • Full regression: 542 passed, 0 failed.
  • Candidate, Validated, Exported, and Sandbox SHA-256 hashes matched.
       │
       ▼
Phase 4: Live Browser Automation & Checkpoint Integrity
  • Live browser demo verified across 16 steps with real screenshots.
  • Active SQLite database confirmed: 1,104 checkpoints across 210 jobs.
  • Failure resilience: 5/5 edge-case scenarios passed.
```

---

## 2. Side-by-Side Comparative Matrix

### 2.1 Benchmark: `samples/discount.py` (21 Lines of Code)

| Metric | Phase 1 (Baseline) | Phase 2 (Intelligent) | Phase 3 (Independent) | Phase 4 (Live Audit) | Overall Improvement |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Discovered Callables** | 1 | 1 | 1 | 1 | — |
| **Callable Coverage** | 100.0% (1/1) | 100.0% (1/1) | 100.0% (1/1) | 100.0% (1/1) | Parity |
| **Generated Test Count** | 2 (or 4 in fallback)| 11 | 11 | 11 | **+9 tests** |
| **Pass Rate on Clean Code**| 100% Pass@1 | 100% Pass@1 | 100% Pass@1 | 100% Pass@1 | 100% Validated |
| **Statement Coverage** | 100.0% (10/10) | 100.0% (10/10) | 100.0% (10/10) | 100.0% (10/10) | Parity (100%) |
| **Total Mutants Generated**| 19 | 19 | 19 | 19 | Standardized |
| **Mutants Killed** | 1 | 17 | 17 | 17 | **+16 killed** |
| **Mutants Survived** | 18 | 2 | 2 | 2 | **-16 survived** |
| **Raw Mutation Score** | **5.26%** | **89.47%** | **89.47%** | **89.47%** | **+84.21%** |
| **Adjusted Mutation Score**| **5.55%** | **94.44%** | **94.44%** | **94.44%** | **+88.89%** |
| **Execution Duration** | 2.1s | 7.64s | 7.14s | 1.16s (sandbox) | Real-time |
| **Suite SHA-256 Digest** | N/A | `eaa41e0b...` | `eaa41e0b...` | `eaa41e0b...` | **Cryptographically Locked** |

---

### 2.2 Benchmark: `samples/uploaded_logistics_engine.py` (240 Lines of Code)

| Metric | Phase 1 (Baseline) | Phase 2 (Intelligent) | Phase 3 (Independent) | Phase 4 (Live Audit) | Overall Improvement |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Discovered Callables** | 10 | 10 | 10 | 10 | Complete Inventory |
| **Eligible Callables Covered**| 1 / 10 (10.0%) | 10 / 10 (100.0%)| 10 / 10 (100.0%)| 10 / 10 (100.0%)| **+90.0% Coverage** |
| **Generated Test Count** | 8 | 64 | 64 | 64 | **+56 tests** |
| **Pass Rate on Clean Code**| 100% Pass@1 | 100% Pass@1 | 100% Pass@1 | 100% Pass@1 | 100% Validated |
| **Statement Coverage** | 42.4% (56/132) | 90.15% (119/132)| 90.15% (119/132)| 90.15% (119/132)| **+47.75% Coverage** |
| **Total Mutants Generated**| 258 | 258 | 258 | 258 | Standardized |
| **Mutants Killed** | 8 | 176 | 176 | 176 | **+168 killed** |
| **Mutants Survived** | 250 | 82 | 82 | 82 | **-168 survived** |
| **Raw Mutation Score** | **3.10%** | **68.22%** | **68.22%** | **68.22%** | **+65.12%** |
| **Adjusted Mutation Score**| **3.42%** | **75.21%** | **75.21%** | **75.21%** | **+71.79%** |
| **Execution Duration** | 12.3s | 17.52s | 18.36s | 18.10s | Real-time Parallel |
| **Suite SHA-256 Digest** | N/A | `c3e17c4d...` | `c3e17c4d...` | `c3e17c4d...` | **Cryptographically Locked** |

---

## 3. The 94.7% UI Metric Reconciliation

A key question an examiner might ask is:
> *"Why did the browser UI display 94.7% during the live demo on discount.py, whereas the offline benchmark report states 89.47% raw and 94.44% adjusted?"*

### The Exact Technical Explanation:
There are **three distinct valid numbers**, each with clear mathematical provenance:

1. **89.47% — The Static Deterministic Raw Score ($17 / 19$):**
   - Produced by the offline, standalone `IntelligentASTSynthesizer`.
   - In this mode, `price=100.0, 90.0, 0.0` are tested. Mutant 18 (`round(final_price, 2) -> round(final_price, 1)`) survives because prices are whole or tenths, yielding identical results under 1 or 2 decimal rounding.
2. **94.44% — The Static Deterministic Adjusted Score ($17 / (19 - 1)$):**
   - Computed by deducting the provably equivalent mutant `MUT_BOUNDARY_SWAP_003` from the denominator:
     $$\frac{17}{18} = 94.444\% \implies 94.44\%$$
3. **94.7% — The Live Dynamic Runtime Score ($18 / 19$):**
   - During the live web application execution (Phase 4), `server.py` invokes the Google ADK generator with the live LLM (Gemini 3.6 Flash) enabled.
   - The LLM synthesizes an unrounded fractional boundary test case (e.g. `price=99.99` or non-integer price), which **kills Mutant 18**!
   - Result: 18 out of 19 mutants killed:
     $$\frac{18}{19} = 94.7368\% \implies \mathbf{94.7\%}$$

### Recommendation for Oral Defense (VIVA):
When presenting to the examiner:
> *"In our offline reproducible benchmark, TestForge achieves an **89.47% raw score** and **94.44% adjusted score** (17/19 killed, 1 equivalent mutant). When run live with the dynamic LLM reflection loop enabled, the generator synthesizes an unrounded price input that kills mutant 18, reaching **18/19 killed (94.7%)** as seen on the live UI dashboard."*

---

## 4. Why Statement Coverage Failed & Mutation Score Succeeded

Consider the Phase 1 Baseline for `discount.py`:
- **Statement Coverage was 100.0% (10/10 statements executed).**
- **Mutation Score was 5.26% (18/19 mutants survived).**

### Why Did This Happen?
The baseline test suite executed every line in `discount.py`, but its assertions were empty:
```python
def test_calculate_discount_nominal():
    res = calculate_discount(100.0, 5, False)
    assert res is not None  # <-- TAUTOLOGY!
```
- When `price <= 0.0` was mutated to `price < 0.0` $\implies$ `res` was still not None $\implies$ test passed.
- When `discount_rate + 0.10` was mutated to `discount_rate + 0.0` $\implies$ `res` was still not None $\implies$ test passed.
- When `final_price = price * (1.0 - discount_rate)` was mutated to `price + 0.0` $\implies$ `res` was still not None $\implies$ test passed.

**The TestForge Solution:**
By synthesizing value-aware assertions (`assert res == pytest.approx(90.0)`), TestForge converted nominal line execution into rigorous defect verification, lifting mutation effectiveness from **5.26% to 89.47% (or 94.7%)**.

