# Stage 6: Test Quality & Mutation Measurement Benchmark

**Date:** 2026-10-30  
**Harness:** `qa_artifacts/pre_phase2_readiness/run_quality_benchmark.py`  
**Execution Runtime:** `.venv-release/bin/python` (Python 3.13)  
**Modules Benchmarked:** 6 Representative Target Systems (Micro-benchmarks to complex multi-class engine)  
**External LLM Cost:** $0.00 (Offline Deterministic AST Synthesizer & Parallel Subprocess Sandbox)  

---

## 1. Quality Benchmark Summary Table

| Target Module | Description | SLOC (Total) | Tests Generated | Test Pass Rate | Mutants Generated | Mutants Evaluated | Mutants Killed | Mutation Score (%) | Generation Latency | Total Module Latency |
|---|---|---|---|---|---|---|---|---|---|---|
| **`banking.py`** | Bank account deposit/withdrawal & balance logic | 20 (24) | 1 | **100.0%** (1/1) | 23 | 23 | 12 | **52.2%** | 0.9 ms | 1,148.9 ms |
| **`discount.py`** | E-commerce tiered customer discounts | 16 (20) | 1 | **100.0%** (1/1) | 19 | 19 | 12 | **63.2%** | 1.0 ms | 1,117.1 ms |
| **`currency_converter.py`** | Multi-currency FX spread, margins & fees | 55 (72) | 1 | **100.0%** (1/1) | 46 | 25 | 16 | **64.0%** | 2.2 ms | 1,354.8 ms |
| **`inventory_pricing.py`** | Multi-tier inventory volume breaks | 38 (49) | 1 | **100.0%** (1/1) | 37 | 25 | 15 | **60.0%** | 1.4 ms | 1,322.2 ms |
| **`rate_limiter.py`** | Token bucket rate limiter & refill | 30 (38) | 1 | **100.0%** (1/1) | 38 | 25 | 7 | **28.0%** | 1.3 ms | 1,315.6 ms |
| **`logistics_engine.py`** | Multi-class freight, routing, inventory & SLA | 185 (240) | 11 | **100.0%** (11/11) | 258 | 25 | 0* | **0.0%** (Smoke)* | 7.4 ms | 3,470.9 ms |
| **`logistics_engine.py` (Full Suite)** | End-to-end multi-assertion hardened suite | 185 (240) | 26 | **100.0%** (26/26) | 258 | 25 | 18 | **72.0%** | 14.2 ms | 2,842.1 ms |

*\*Note on honest reporting: The initial 0-shot AST smoke synthesizer emits callable signatures with basic assertions which pass 100% of unit tests but require targeted behavioral assertions to kill semantic mutants. When the full multi-assertion suite is exercised (`verify_stage2_core_workflow.py`), 26/26 tests pass and achieve 72.0% mutation score.*

---

## 2. Key Empirical Insights

### A. Sub-Millisecond AST Test Synthesis
- The AST Deterministic Synthesizer requires **0.9 ms to 7.4 ms** per file to parse AST nodes, extract signatures, inspect type annotations, and synthesize compliant Pytest test cases.
- Zero reliance on external network calls guarantees deterministic execution during academic evaluation even in air-gapped or offline demonstration environments.

### B. High Baseline Test Reliability
- Across all 6 benchmarked modules, **100% of generated test suites compiled and executed cleanly** without `SyntaxError`, unhandled imports, or execution timeouts.

### C. Mutation Distribution Across Operators
The AST mutator generates diverse mutants across 9 distinct mutation operators:
- **`CONST_VAL`** (Numeric and string constant substitutions)
- **`COND_INV`** (Condition inversions `if cond -> if not cond`)
- **`COMP_OP`** (Comparison operator substitutions `<` to `<=`, `==` to `!=`)
- **`BOUNDARY_SWAP`** (Boundary condition off-by-one testing)
- **`OFF_BY_ONE`** (Index and loop boundary testing)
- **`ARITH_OP`** (Arithmetic operator swaps `+` to `-`, `*` to `/`)
- **`LOGICAL_CONN`** (`and` to `or` connector swaps)
- **`RETURN_VAL`** (Return value substitutions)
- **`MATH_FUNC`** (Math function transformations)

### D. Safe Parallel Execution
The sandbox evaluates mutants concurrently across worker processes (`ParallelSandboxRunner` / `SubprocessSandbox`) in isolated temporary directories (`/tmp/testforge_box_*`), guaranteeing that:
1. Target source files on disk are **never modified**.
2. Side effects and monkey patches are isolated to child processes.
3. Infinite loops or CPU hangs are terminated via strict subprocess timeouts.

