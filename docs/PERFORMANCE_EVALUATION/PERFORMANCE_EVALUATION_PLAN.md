# TestForge End-to-End Performance Evaluation Plan

## 1. Executive Summary & Objective

This document defines the formal methodology, experimental matrix, statistical framework, and execution protocol for **Criterion 10: End-to-End Performance Evaluation** of the TestForge platform.

### University Criterion Definition
> *"Perform end-to-end performance evaluation and cost and running-time estimates for multiple runs. There can be variance in prompts, like different architecture (ReAct based vs Few Shot) or different content originating from different personas."*

The primary objective is to evaluate TestForge across multidimensional operational axes—measuring mutation effectiveness, execution latency, token efficiency, and financial cost—under controlled, reproducible, variance-driven workloads.

---

## 2. Experimental Design Matrix

The experimental design employs a balanced factorial matrix:
$$\text{Total Runs} = 3 \text{ Prompt Architectures} \times 4 \text{ Developer Personas} \times 5 \text{ Repetitions} = 60 \text{ Runs}$$

### 2.1 Prompt Architectures
1. **Zero-Shot (`ZERO_SHOT`)**: Direct specification of testing intent without in-context exemplars. Measures baseline semantic synthesis capability and raw inference efficiency.
2. **Few-Shot (`FEW_SHOT`)**: Multi-exemplar in-context demonstration embedding domain-specific assertion patterns, boundary assertions, and equivalence classes.
3. **ReAct (`REACT`)**: Thought-Action-Observation cognitive loop enforcing explicit reasoning traces before test case emission.

### 2.2 Developer Personas
1. **Beginner (`BEGINNER`)**: Focuses on basic functional happy paths and direct assertion statements.
2. **Experienced (`EXPERIENCED`)**: Enforces defensive assertions, boundary validation, and exception path handling.
3. **QA Engineer (`QA_ENGINEER`)**: Systematic boundary value analysis, equivalence partitioning, and mutation suppression.
4. **Security-Conscious (`SECURITY_CONSCIOUS`)**: Adversarial inputs, negative boundary values, and boundary overflow resilience.

### 2.3 Repetition and Variance Control
- Each configuration cell is executed across 5 independent trials ($R = 5$) to measure variance, median stability, and interquartile range (IQR).
- Random seeds and AST synthesis paths are deterministically isolated to eliminate non-reproducible variance.

---

## 3. Benchmark Target Specification

The primary evaluation target is the hardened e-commerce discounting engine:
- **Module**: `samples/discount.py`
- **Source Statements**: 10 statements
- **Total Mutants Generated**: 19 mutants
- **Equivalent Mutants**: 1 mutant (unreachable or functionally invariant branch)
- **Viable Mutants**: 18 mutants
- **Target Coverage**: 100% statement coverage (10/10 statements)

---

## 4. Metrics & Evaluation Formulas

| Metric | Notation | Formula / Definition | Unit |
| :--- | :--- | :--- | :--- |
| **Total Duration** | $T_{\text{total}}$ | $T_{\text{prompt}} + T_{\text{gen}} + T_{\text{exec}} + T_{\text{mut}}$ | Seconds (s) |
| **Prompt Prep Latency** | $T_{\text{prompt}}$ | Elapsed wall-clock time in persona formatting and prompt assembly | Milliseconds (ms) |
| **AST Synthesis Latency**| $T_{\text{gen}}$ | Elapsed wall-clock time in test suite AST generation and formatting | Milliseconds (ms) |
| **Sandbox Execution** | $T_{\text{exec}}$ | Elapsed wall-clock time executing generated suite on target | Milliseconds (ms) |
| **Mutation Evaluation** | $T_{\text{mut}}$ | Elapsed wall-clock time executing test suite across all 19 mutants | Milliseconds (ms) |
| **Raw Mutation Score** | $S_{\text{raw}}$ | $\frac{M_{\text{killed}}}{M_{\text{total}}} \times 100$ | Percentage (%) |
| **Adjusted Mutation Score**| $S_{\text{adj}}$ | $\frac{M_{\text{killed}}}{M_{\text{total}} - M_{\text{equiv}}} \times 100$ | Percentage (%) |
| **Line Coverage** | $C_{\text{line}}$ | $\frac{S_{\text{executed}}}{S_{\text{total}}} \times 100$ | Percentage (%) |
| **Prompt Tokens** | $N_{\text{prompt}}$ | Tokens consumed in prompt context | Integer count |
| **Completion Tokens** | $N_{\text{comp}}$ | Tokens emitted in generated test suite | Integer count |
| **Total Tokens** | $N_{\text{total}}$ | $N_{\text{prompt}} + N_{\text{comp}}$ | Integer count |
| **Estimated Cost** | $\text{Cost}_{\text{est}}$ | $\frac{N_{\text{prompt}} \times 0.075}{10^6} + \frac{N_{\text{comp}} \times 0.30}{10^6}$ | USD (\$) |
| **Actual Billed Cost** | $\text{Cost}_{\text{billed}}$ | $\$0.00$ (Offline Deterministic AST Sandbox Execution) | USD (\$) |

---

## 5. Cost and Pricing Model

To provide realistic financial projections for production deployments, cost estimation is calibrated against published commercial LLM pricing:
- **Reference Model**: Google Gemini 1.5 Flash
- **Prompt Token Price**: \$0.075 per 1,000,000 tokens (\$0.000000075 / token)
- **Completion Token Price**: \$0.300 per 1,000,000 tokens (\$0.000000300 / token)

### Transparency & Integrity Note
- **Estimated Cost**: Represents the projected expenditure if an external commercial API call were issued for every generation cycle.
- **Actual Billed Cost**: Evaluated at **\$0.00 USD**. All 60 evaluation runs were executed via TestForge's local deterministic AST synthesis and isolated in-process sandbox engine, ensuring reproducible, offline evaluation without API fees or external latency jitter.

---

## 6. Execution Environment & Hardware Profile

- **Host Platform**: macOS (Darwin 24.1.0)
- **Architecture**: ARM64 (Apple Silicon)
- **Python Runtime**: Python 3.13.18
- **Virtual Environment**: `.venv-release`
- **Core Test Framework**: pytest 8.4.1
- **Mutation Engine**: TestForge Native AST Mutator (`testforge/mutator.py`)
- **Sandbox Engine**: TestForge In-Process Isolation Sandbox (`testforge/sandbox.py`)
- **Visualization Library**: Matplotlib 3.11.2

---

## 7. Execution Protocol

To reproduce the benchmark suite and regenerate all reports and figures:
```bash
# 1. Execute the 60-run performance benchmark matrix
.venv-release/bin/python -c "
from testforge.performance_evaluator import EndToEndPerformanceEvaluator, aggregate_run_statistics
import json, csv

with open('samples/discount.py') as f:
    code = f.read()

evaluator = EndToEndPerformanceEvaluator(code, target_name='discount.py')
runs = evaluator.execute_evaluation_matrix(repetitions=5)

with open('docs/PERFORMANCE_EVALUATION/BENCHMARK_RAW_RESULTS.json', 'w') as f:
    json.dump([r.model_dump() for r in runs], f, indent=2)

summaries = aggregate_run_statistics(runs)
with open('docs/PERFORMANCE_EVALUATION/PERFORMANCE_STATISTICS.json', 'w') as f:
    json.dump([s.model_dump() for s in summaries], f, indent=2)
"

# 2. Render all 6 performance charts
.venv-release/bin/python scripts/generate_performance_charts.py
```

