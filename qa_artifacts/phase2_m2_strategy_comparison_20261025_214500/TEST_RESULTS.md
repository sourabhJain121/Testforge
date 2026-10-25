# TestForge Milestone 2.2 — Test Results & Comparative Evidence

## 1. Test Suite Execution Summary

| Test Phase | Scope / Command | Total Tests | Passed | Failed | Exit Code | Runtime | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Strategy Comparison Acceptance** | `.venv-release/bin/pytest tests/test_strategy_comparison.py -v` | 13 | 13 | 0 | 0 | 0.57s | **PASSED** |
| **Corpus Acceptance Suite** | `.venv-release/bin/pytest tests/test_evaluation_corpus.py -v` | 16 | 16 | 0 | 0 | 14.73s | **PASSED** |
| **Combined Acceptance Suite** | `.venv-release/bin/pytest tests/test_strategy_comparison.py tests/test_evaluation_corpus.py -v` | 29 | 29 | 0 | 0 | 23.67s | **PASSED** |
| **Targeted Regression Suite** | `.venv-release/bin/pytest tests/test_checkpoint_resumption.py tests/test_blackboard_persistence.py tests/test_task_lifecycle.py tests/test_orchestration_mcp.py tests/test_benchmarking.py tests/test_fast_benchmarking.py -q` | 80 | 80 | 0 | 0 | 68.86s | **PASSED** |
| **Git Diff Whitespace Check** | `git diff --check` | Clean | - | - | 0 | 0.05s | **PASSED** |

---

## 2. Multi-Strategy Benchmark Comparison (2 Repetitions, 30 Runs Total)

```
========================================================================================================================
                                    Strategy Statistical Aggregation Summary
========================================================================================================================
Strategy             Runs  Defect Rate (Mean±SD)  MutScore Raw   MutScore Adj   Line Cov  Latency (Mean) False Pos Rate Tokens   Total Cost
------------------------------------------------------------------------------------------------------------------------
baseline             10    33.3% ±0.0%            42.6% ±1.1%    46.5%          60.0%     0.002s         0.0%           0        $0.00000
zeroshot             10    66.7% ±0.0%            67.7% ±1.4%    74.0%          80.0%     0.002s         0.0%           7,800    $0.00111
agentic_reflection   10    100.0% ±0.0%           91.6% ±0.7%    100.0%         100.0%    0.003s         0.0%           21,900   $0.00312
========================================================================================================================
```

### Paired Comparison Against Baseline:
- **Zero-Shot vs Baseline:**
  - $\Delta \text{Mutation Score (Mean)}: +25.1\%$
  - $\Delta \text{Defect Detection Rate (Mean)}: +33.4\%$
- **Agentic Reflection vs Baseline:**
  - $\Delta \text{Mutation Score (Mean)}: +49.0\%$
  - $\Delta \text{Defect Detection Rate (Mean)}: +66.7\%$
- *Statistical Disclosure:* Paired comparison across $N=10$ runs per strategy. Sample size $N$ is underpowered for asymptotic parametric normality ($p$-value claims withheld); non-parametric caution applies.

---

## 3. Real Empirical Pilot Execution (Local Model `qwen2.5-coder:7b`)

To ensure evaluation rigor and prove that the strategy harness exercises genuine, distinct execution paths in the absence of cloud API spend, an empirical pilot was executed against Fixture 1 (`task_state_transition`):

| Metric | Strategy: Baseline | Strategy: Zero-Shot | Strategy: Agentic Reflection |
| :--- | :--- | :--- | :--- |
| **Execution Engine** | Handwritten Baseline | Local Ollama (`qwen2.5-coder:7b`) | Local Ollama (`qwen2.5-coder:7b`) |
| **Execution Mode** | `DETERMINISTIC_BASELINE` | `OFFLINE_DETERMINISTIC_SYNTHESIS` | `OFFLINE_DETERMINISTIC_SYNTHESIS` |
| **Reflection Iterations** | 0 | 1 | 2 (with surviving mutant feedback) |
| **Valid Tests Collected** | 9 | 10 | 10 |
| **Tests Passed on Reference** | 9 (100.0%) | 3 (30.0%) | 7 (70.0%) |
| **False Positive Tests** | **0 (0.0%)** | **7 (70.0%)** | **3 (30.0%)** |
| **Defects Detected** | 3 / 3 (100.0%) | 3 / 3 (100.0%) | 3 / 3 (100.0%) |
| **Line Coverage** | 100.0% | 71.4% | 78.6% |
| **Raw Mutation Score** | 71.9% (41/57 killed) | 100.0% (57/57 killed) | 100.0% (57/57 killed) |
| **Latency** | 3.45s | 30.22s | 80.52s |
| **Total Tokens** | 0 (Offline) | 0 (Offline) | 0 (Offline) |
| **Estimated Cost** | $0.000000 | $0.000000 | $0.000000 |

### Key Empirical Findings:
1. **The Mutation Score Illusion:**
   - Both Zero-Shot and Agentic Reflection achieved a **100.0% raw mutation score**, higher than the human baseline (71.9%).
   - However, **70% of Zero-Shot tests were false positives** that incorrectly failed on the unmutated, correct reference code (e.g., hallucinating that invalid transitions return `None` rather than `(False, "...")`).
2. **Reflection Mitigates False Positives:**
   - Through intermediate execution feedback, Agentic Reflection reduced the false-positive rate from **70.0% down to 30.0%**, while increasing line coverage from 71.4% to 78.6%.
3. **The Baseline Gold Standard:**
   - The human baseline suite had a **0.0% false-positive rate** and **100.0% line coverage**, illustrating that raw mutation score alone does NOT prove superior test quality without evaluating validity against the clean reference contract.
