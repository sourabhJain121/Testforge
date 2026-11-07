# TestForge — Evaluation Methodology, Metrics & Mathematical Formulas

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Primary Source Modules:** `testforge/mutator.py`, `testforge/equivalence.py`, `testforge/benchmarking.py`, `testforge/performance_evaluator.py`  

---

## 1. Multi-Dimensional Evaluation Framework

TestForge is evaluated across seven rigorous technical dimensions:
1. **Functional Testing:** Unit, integration, regression, and browser automation suites.
2. **Code Statement Coverage:** Statement and branch coverage across the TestForge engine.
3. **Mutation Testing:** Fault-revealing capability evaluated on realistic target modules.
4. **Security Guardrails:** Deterministic attack injection resistance across personas and architectures.
5. **End-to-End Performance:** Empirical runtime, token consumption, and cost benchmarking.
6. **Observability & Telemetry:** Precise accounting separating provider tokens from heuristic estimates.
7. **Durable Persistence:** Checkpoint integrity and time-travel rollback validation.

---

## 2. Mathematical Formulas & Metric Definitions

### 1. Statement Coverage
Measures the proportion of executable Python statements executed by the test suite:
$$\text{Statement Coverage (\%)} = \left( \frac{\text{Statements Executed}}{\text{Total Executable Statements}} \right) \times 100$$
- **Measurement Tool:** `coverage.py` via `pytest --cov=testforge`.
- **Verified Result:** **81.33% statement coverage** across the core TestForge engine.

### 2. Raw Mutation Score
Measures the proportion of viable synthetic mutants killed by the test suite:
$$\text{Raw Mutation Score (\%)} = \left( \frac{\text{Mutants Killed}}{\text{Total Viable Mutants Generated}} \right) \times 100$$
- Where:
  - $\text{Total Mutants} = \text{Killed Mutants} + \text{Surviving Mutants} + \text{Timed-Out Mutants}$.
  - Invalid mutants (those failing Python syntax compilation) are rejected during generation and never enter the denominator.

### 3. Adjusted Mutation Score
Corrects the mutation score by excluding verified equivalent mutants:
$$\text{Adjusted Mutation Score (\%)} = \left( \frac{\text{Mutants Killed}}{\text{Total Viable Mutants} - \text{Verified Equivalent Mutants}} \right) \times 100$$
- **Strict Conservation Rule:** In `testforge/equivalence.py`, a mutant is **never** classified as equivalent simply because it survived test runs. Equivalent classification requires rigorous proof (syntactic AST identity, self-canceling transforms, or provable dead-code mutation).

### 4. Mean Benchmark Latency
$$\text{Mean Latency (seconds)} = \frac{1}{N} \sum_{i=1}^{N} \text{Duration}_i$$
- Where $N$ is the number of experimental repetitions per matrix cell ($N=5$).

### 5. Estimated Token Cost Formula
$$\text{Estimated Cost (USD)} = \frac{\text{Prompt Tokens} \times P_{\text{prompt}} + \text{Completion Tokens} \times P_{\text{comp}}}{1,000,000}$$
- **Reference Model:** Google Gemini 1.5 Flash published rates:
  - $P_{\text{prompt}} = \$0.075$ per 1,000,000 tokens.
  - $P_{\text{comp}} = \$0.300$ per 1,000,000 tokens.
- **Actual Billed Cost:** **$0.00 USD** (Runs in automated CI execute via offline AST synthesizer).

---

## 3. Verified Empirical Results

### Summary Scorecard

| Evaluation Dimension | Metric / Target | Baseline State | Final Hardened State | Status | Source Evidence |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Functional Tests** | Regression Suite Pass Count | 542 passed | **611 passed, 0 failed** | **EXCEEDED** | `pytest tests/ -q` (378.65s) |
| **Engine Coverage** | Statement Coverage | ~62.0% | **81.33%** | **SATISFIED** | `.coverage` database / HTML report |
| **Discount Module** | Raw Mutation Score | 5.26% (1/19) | **89.47% (17/19 killed)** | **EXCEEDED** | `samples/discount_module.py` |
| **Discount Module** | Adjusted Mutation Score | 5.26% (1/19) | **94.44% (17/18 non-eq)** | **EXCEEDED** | Excludes 1 dead-code mutant |
| **Logistics Module**| Raw Mutation Score | 3.10% (8/258) | **68.22% (176/258 killed)**| **EXCEEDED** | `samples/logistics_module.py` |
| **Logistics Module**| Adjusted Mutation Score | 3.10% (8/258) | **75.21% (176/234 non-eq)**| **EXCEEDED** | Excludes 24 verified equivalent |
| **Security Guardrails**| Attack Defense Rate (Criterion 8)| Incomplete | **100% Defense (120 trials)**| **COMPLETE** | `docs/SECURITY_EVALUATION/` |
| **Performance Benchmark**| Empirical Runs (Criterion 10) | Incomplete | **60 runs (12 matrix cells)** | **COMPLETE** | `BENCHMARK_RAW_RESULTS.json` |
| **Observability** | Actual LLM Tokens Reported | 0 | **29,476 actual tokens** | **VERIFIED** | `testforge_trace.jsonl` |
| **Observability** | Estimated Deterministic Tokens | 0 | **27,920 estimated tokens**| **VERIFIED** | Deterministic calls contribute 0 actual |
| **Persistence** | SQLite Checkpoint Integrity | 1,223 rows | **1,310 verified checkpoints**| **INTACT** | `qa_artifacts/testforge_checkpoints.db` |

---

## 4. Deep Dive: Mutation Score Progression

### Discount Module Hardening (`samples/discount_module.py`)
- **Total Mutants Generated:** 19 mutants
- **Baseline Test Suite:** 1 test $\rightarrow$ Killed 1 mutant (5.26% raw score).
- **Iteration 1 (AST Synthesis):** Generated boundary parametrization $\rightarrow$ Killed 15 mutants (78.95% raw score).
- **Iteration 2 (Adversarial Reflection):** Critic diagnosed surviving boundary transitions at quantity 5 and 10 $\rightarrow$ Generated targeted boundary asserts $\rightarrow$ **Killed 17 mutants (89.47% raw score)**.
- **Equivalent Mutant Analysis:**
  - 1 mutant mutated an AST statement inside an unreachable defensive block.
  - Provable equivalent mutant excluded from denominator: $19 - 1 = 18$ viable mutants.
  - **Adjusted Mutation Score:** $\frac{17}{18} \times 100 = \mathbf{94.44\%}$.

### Logistics Module Hardening (`samples/logistics_module.py`)
- **Total Mutants Generated:** 258 mutants across complex multi-branch logistics calculations (freight tiers, hazardous cargo handling, volumetric weights, international customs tariffs).
- **Baseline Test Suite:** Killed 8 mutants (3.10% raw score).
- **Hardened Test Suite (`test_hardened.py`):**
  - Generated comprehensive parametric matrices, boundary exceptions, and stateful lifecycle tests for `WarehouseInventory`.
  - **Killed 176 mutants (68.22% raw score)**.
- **Equivalent Mutant Analysis:**
  - 24 mutants provably identified as equivalent (syntactic identity under commutative operations and unreachable defensive exception clauses).
  - Non-equivalent viable mutants: $258 - 24 = 234$.
  - **Adjusted Mutation Score:** $\frac{176}{234} \times 100 = \mathbf{75.21\%}$.

