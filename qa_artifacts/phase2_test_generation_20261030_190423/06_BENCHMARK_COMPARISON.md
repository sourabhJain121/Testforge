# Report 06: Controlled Benchmark Comparison (Phase 1 Baseline vs. Phase 2)

**Artifact Directory**: `qa_artifacts/phase2_test_generation_20261030_190423/`  
**Evaluation Phase**: Phase 2 — Intelligent Multi-Callable Test Generation & Refinement  
**Status**: EMPIRICALLY BENCHMARKED & VERIFIED  
**Date**: October 30, 2026  

---

## 1. Executive Summary

This report establishes the empirical comparison between the **Phase 1 Baseline** (established in `qa_artifacts/post_ast_mutation_baseline_20261030_185148/`) and the **Phase 2 Intelligent Generator** on the two standardized benchmark targets:
1. `samples/discount.py` (Simple single-callable module with branching)
2. `samples/uploaded_logistics_engine.py` (Complex multi-callable module with classes, state, and domain logic)

The results demonstrate an extraordinary, technically defensible improvement in mutation score, callable coverage, and oracle strength without fabricating scores or modifying the target source code.

---

## 2. Comprehensive Metric Comparison Table

### Target 1: `samples/discount.py` (20 LOC)

| Metric | Phase 1 Baseline | Phase 2 Execution | Absolute Delta | Relative Gain |
|---|---|---|---|---|
| **Discovered Callables** | 1 | 1 | 0 | 0.0% |
| **Eligible Callables** | 1 | 1 | 0 | 0.0% |
| **Tested Callables** | 1 | 1 | 0 | 0.0% |
| **Callable Coverage %** | 100.0% | 100.0% | 0.0% | 0.0% |
| **Generated Tests** | 4 | 11 | +7 | +175.0% |
| **Meaningful Assertions** | 4 | 11 | +7 | +175.0% |
| **Invariant Assertions (`not None`)** | 0 | 0 | 0 | 0.0% |
| **Boundary Tests ($T, T-1, T+1$)** | 2 | 9 | +7 | +350.0% |
| **Negative Tests (`pytest.raises`)** | 0 | 0 | 0 | 0.0% |
| **Sandbox Clean Pass Rate (Pass@1)** | 100.0% (4/4) | 100.0% (11/11) | 0.0% | 0.0% |
| **Target Line Coverage** | 100.0% (10/10) | 100.0% (10/10) | 0.0% | 0.0% |
| **AST Mutants Injected** | 19 | 19 | 0 | 0.0% |
| **Mutants Killed** | 1 | **17** | **+16** | **+1600.0%** |
| **Mutants Survived** | 18 | **2** | **-16** | **-88.9%** |
| **Mutation Score %** | **5.26%** | **89.47%** | **+84.21%** | **+1600.0%** |

---

### Target 2: `samples/uploaded_logistics_engine.py` (240 LOC)

| Metric | Phase 1 Baseline | Phase 2 Execution | Absolute Delta | Relative Gain |
|---|---|---|---|---|
| **Discovered Callables** | 10 | 10 | 0 | 0.0% |
| **Eligible Callables** | 10 | 10 | 0 | 0.0% |
| **Tested Callables** | 1 | **10** | **+9** | **+900.0%** |
| **Callable Coverage %** | 10.0% | **100.0%** | **+90.0%** | **+900.0%** |
| **Generated Tests** | 11 | **64** | **+53** | **+481.8%** |
| **Meaningful Assertions** | 3 | **67** | **+64** | **+2133.3%** |
| **Invariant Assertions (`not None`)** | 8 | **0** | **-8** | **-100.0% (Eliminated)** |
| **Boundary Tests ($T, T-1, T+1$)** | 0 | **43** | **+43** | **+$\infty$** |
| **Negative Tests (`pytest.raises`)** | 0 | **10** | **+10** | **+$\infty$** |
| **Sandbox Clean Pass Rate (Pass@1)** | 100.0% (11/11) | 100.0% (64/64) | 0.0% | 0.0% |
| **Target Line Coverage** | 22.7% (30/132) | **90.2% (119/132)** | **+67.5%** | **+297.4%** |
| **AST Mutants Injected** | 258 | 258 | 0 | 0.0% |
| **Mutants Killed** | 8 | **176** | **+168** | **+2100.0%** |
| **Mutants Survived** | 250 | **82** | **-168** | **-67.2%** |
| **Mutation Score %** | **3.10%** | **68.22%** | **+65.12%** | **+2100.6%** |

---

## 3. Visual Representation of Progress

```
================================================================================
                    MUTATION TESTING KILL RATE COMPARISON
================================================================================

Target: discount.py
  Phase 1 Baseline : [■                   ]  5.26% (1/19 killed)
  Phase 2 Synthesis: [■■■■■■■■■■■■■■■■■■  ] 89.47% (17/19 killed)  [+84.21%]

Target: uploaded_logistics_engine.py
  Phase 1 Baseline : [                    ]  3.10% (8/258 killed)
  Phase 2 Synthesis: [■■■■■■■■■■■■■■      ] 68.22% (176/258 killed) [+65.12%]

================================================================================
```

---

## 4. Root Causes for Score Elevation

1. **Resolution of the Single-Callable Blocker**:
   - In Phase 1, only `calculate_item_discount` was tested. The other 9 callables (covering ~80% of lines) had zero tests, guaranteeing that 200+ mutants survived untouched.
   - In Phase 2, coverage rose to 100% of eligible callables (6 functions + 4 methods), lifting line coverage from 22.7% to 90.2%.
2. **Replacement of Invariant Assertions with Precise Oracles**:
   - The 8 generic `assert res is not None` assertions in Phase 1 were completely replaced with 67 exact value, approx, and boolean assertions.
3. **Automated Boundary Stress ($T \pm 1$)**:
   - 43 boundary tests actively stressed edge conditions, killing relational operator mutants that survive nominal tests.
4. **Exception Guard Verification (`pytest.raises`)**:
   - 10 negative tests verified that missing guards raise errors, killing guard-deletion mutants immediately.

