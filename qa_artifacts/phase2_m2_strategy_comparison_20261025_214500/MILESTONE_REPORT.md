# TestForge Phase 2 — Milestone 2.2 Report
## Empirical Comparison of Baseline, Zero-Shot, and Agentic Reflection (GAP-05)

**Milestone Identifier:** `phase2_m2_strategy_comparison_20261025_214500`  
**Execution Date:** October 25, 2026  
**Repository:** `/Users/sourabh/TestForge`  
**Target Gap:** GAP-05 (Empirical Strategy Comparison & Statistical Calibration)  
**Status:** **COMPLETE & VERIFIED**

---

## 1. Executive Summary

Milestone 2.2 resolves **GAP-05** by implementing a reproducible empirical comparison harness that systematically evaluates three distinct test-generation strategies across the five evaluation corpus fixtures:
1. **Baseline (`baseline`):** Documented, human-authored baseline unit tests.
2. **Zero-Shot Synthesis (`zeroshot`):** Single-pass autonomous test generation via `TestGeneratorAgent` without iterative feedback.
3. **Agentic Reflection (`agentic_reflection`):** Multi-agent mutation-guided reflection loop with intermediate execution feedback and AST fault refinement.

The comparison harness enforces rigorous metric categorization (Measured, Calculated, Estimated), strict denominator accounting (excluding invalid mutants), false-positive detection against clean reference code, and a strict no-fabrication policy for token and cost metrics.

All 13 new acceptance tests in `tests/test_strategy_comparison.py`, all 16 corpus acceptance tests in `tests/test_evaluation_corpus.py` (29 total acceptance tests), and all 80 targeted regression tests passed cleanly with zero failures.

---

## 2. Which Strategies Actually Ran

All three target strategies were exercised through their genuine, distinct execution paths:

| Strategy | Execution Mechanism | Reflection Iterations | Prompt Variant |
| :--- | :--- | :--- | :--- |
| **`baseline`** | Direct execution of static corpus baseline suite in sandbox | 0 | `baseline-handwritten-v1` |
| **`zeroshot`** | Autonomous generation via `TestGeneratorAgent` (Iteration 0) | 1 | `zero-shot-synthesis-v1` |
| **`agentic_reflection`** | Multi-pass loop: initial synthesis $\to$ sandbox mutation evaluation $\to$ surviving mutant AST diff reflection $\to$ refined synthesis | 2 | `multi-agent-reflection-v1` |

---

## 3. Which Results Are Real, Mocked, or Simulated

1. **Simulated / Mocked (`SIMULATED_FAST_MOCK`):**
   - Executed via `--fast` mode across all 5 fixtures $\times$ 3 strategies $\times$ 2 repetitions (30 total runs).
   - Used for rapid CI/CD regression verification (< 0.01s per run).
   - Explicitly tagged with `is_simulated=True`, `execution_mode="SIMULATED_FAST_MOCK"`, and transparent disclaimers.

2. **Empirical Local Model Execution (`OFFLINE_DETERMINISTIC_SYNTHESIS`):**
   - Executed against Fixture 1 (`task_state_transition`) using local Ollama model `qwen2.5-coder:7b`.
   - Real, un-mocked neural network code generation, AST parsing, sandbox execution, and mutation evaluation.
   - Accurately recorded real wall-clock latency (30.2s for zero-shot, 80.5s for agentic reflection), real false-positive tests, and zero fabricated cloud tokens.

3. **Live Cloud API Execution (`LIVE_MODEL_PILOT`):**
   - Marked as **BLOCKED pending explicit user authorization**.
   - No unauthorized API calls or charges were made against commercial providers.

---

## 4. Key Empirical Findings & Strategy Quality Insights

The empirical pilot provided a crucial insight regarding automated test evaluation:

| Strategy | Mutation Score (Raw) | Defects Detected | Line Coverage | False Positives | False Positive Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline** | 71.9% | 3 / 3 (100.0%) | 100.0% | **0** | **0.0%** |
| **Zero-Shot** | 100.0% | 3 / 3 (100.0%) | 71.4% | **7** | **70.0%** |
| **Agentic Reflection** | 100.0% | 3 / 3 (100.0%) | 78.6% | **3** | **30.0%** |

### Critical Scientific Deductions:
1. **The Fallacy of Raw Mutation Score:** A 100% mutation score does NOT prove superior real-world test quality. Zero-shot achieved 100% mutation score primarily because 70% of its assertions were overly strict or hallucinated, causing them to fail on both mutants *and* the clean reference code.
2. **Value of Agentic Reflection:** Intermediate sandbox execution feedback allowed the agentic reflection loop to catch contract violations, reducing the false positive rate from **70.0% to 30.0%** and increasing line coverage from **71.4% to 78.6%**.
3. **The Human Baseline Standard:** Human-written baseline suites maintained a **0.0% false-positive rate** and **100.0% line coverage**, underscoring that valid test engineering requires balancing mutant kill power against specification fidelity.

---

## 5. Test Outcomes & Evidence Paths

### Test Suite Execution:
- **`pytest tests/test_strategy_comparison.py tests/test_evaluation_corpus.py -v`**:
  - **29 passed in 23.67s (Exit code 0)**.
- **Targeted Regression Suites**:
  - **80 passed in 68.86s (Exit code 0)**.
- **`git diff --check`**:
  - **Clean (Exit code 0)**.

### Evidence Directory:
`/Users/sourabh/TestForge/qa_artifacts/phase2_m2_strategy_comparison_20261025_214500/`

- `MILESTONE_REPORT.md`: This completion audit report.
- `EXPERIMENT_PROTOCOL.md`: Controlled experimental methodology and execution settings.
- `STRATEGY_COMPARISON.csv`: Machine-readable tabular run records across all 30 benchmark runs.
- `RAW_RUN_RESULTS.json`: Complete serialized run logs, telemetry, and statistical summaries.
- `METRIC_DEFINITIONS.md`: Mathematical definitions and denominator accounting formulas.
- `TEST_RESULTS.md`: Detailed test command outputs and empirical pilot comparisons.
- `IMPLEMENTATION_TRACEABILITY.csv`: Requirement-to-test verification matrix.
- `KNOWN_LIMITATIONS.md`: Safe operational boundaries, sample size limits, and proposed live campaign parameters.

---

## 6. Milestone Conclusion & Stop Condition

Milestone 2.2 is **COMPLETE**. The strategy comparison harness is fully operational, reproducible, and mathematically verified. In accordance with instructions, execution has halted here without initiating Phase 3.
