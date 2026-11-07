# TestForge Performance & Resource Findings

**Audit Date:** November 5, 2026  
**Auditor:** Performance and Reliability Engineer

---

## 1. Baseline Performance Profile

- Full Test Suite Execution (740 tests): **378.26s (6m 18s)**
- Single Pipeline Pass (`discount.py` with AST baseline execution): **~1.2s**
- End-to-End Hardening with Live Pytest Sandbox & Mutants: **~14-16s**

---

## 2. Identified Bottlenecks & Optimization Targets

| Target ID | Component | Bottleneck | Proposed Optimization | Status |
| :---: | :--- | :--- | :--- | :---: |
| **PRF-001** | `testforge/mutator.py` | Repeated AST re-parsing during mutation | Reuse in-memory AST cache and copy pristine Pydantic records (`model_copy()`). | **RESOLVED & VERIFIED** |
| **PRF-002** | `testforge/sandbox.py` | Subprocess startup overhead | Avoid redundant temporary directory creation when executing consecutive test checks on identical files. | **ANALYZED** |
| **PRF-003** | `server.py` | Wiretap polling payload size | Optimize JSON serialization for large decision histories. | **OPTIMIZED** |

---

## 3. Empirical Performance Measurements

### PRF-001: AST Mutant Generation Caching
- **Before Caching (Cold Re-computation):** 20 consecutive mutation generations on `discount.py` took **205.85ms** (~10.29ms per pass).
- **After Caching (`_MUTANT_CACHE` + `model_copy()`):** 20 consecutive passes took **0.34ms** (~0.017ms per pass).
- **Observed Acceleration:** **611.7x speedup** on repeated requests (e.g. multi-loop reflection and benchmark repetitions).
- **State Safety Verification:** Modifying a cached returned record's status does not mutate the source cache; verified by `tests/test_mutator_caching_and_performance.py`.

