# TestForge Phase 4.1 — Baseline Metrics & Empirical Foundation

**Timestamp**: 2026-10-26T10:36:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Data Sources**:
- `qa_artifacts/phase2_m1_evaluation_corpus_20261025_211500/benchmark_corpus_results.json`
- `qa_artifacts/phase2_m2_strategy_comparison_20261025_214500/STRATEGY_COMPARISON.csv`

---

## 1. Summary of Established Baseline Metrics

Across the 5 evaluation fixtures (15 controlled defects, 201 total generated AST mutants), the existing system exhibits the following performance across strategies:

| Metric | Condition A: Baseline (Handwritten) | Condition B: Zero-Shot (Single-Pass LLM) | Condition C: Agentic Reflection (TestForge) |
| :--- | :---: | :---: | :---: |
| **Defect Detection Rate** | 5 / 15 (33.3%) | 10 / 15 (66.7%) | **15 / 15 (100.0%)** |
| **Average Raw Mutation Score** | 43.1% | 67.8% | **91.4%** |
| **Average Adjusted Mutation Score** | 46.9% | 74.3% | **100.0%** |
| **Line Coverage** | 76.5% | 88.4% | **98.2%** |
| **Reflection Iterations** | 0 (static) | 1 | 2 to 3 |
| **Mean Execution Latency** | ~0.002s (offline) | ~18.5s (LLM) | ~42.8s (LLM) |
| **Clean Code Pass Rate (pass@1)** | 100.0% | 85.0% (initial) -> 100% | 100.0% |

---

## 2. Per-Fixture Breakdown (Condition Baseline vs Zero-Shot vs Reflection)

### Fixture 1: `task_state_transition`
- **Source Code**: 48 lines | **Controlled Defects**: 3 (`DEFECT-SM-001`, `002`, `003`)
- **Total Mutants**: 28 | **Verified Equivalent**: 2
- **Baseline**:
  - Defects Detected: 1 / 3 (33.3%)
  - Raw Mutation Score: 42.9% | Adjusted Score: 46.2%
- **Zero-Shot**:
  - Defects Detected: 2 / 3 (66.7%)
  - Raw Mutation Score: 67.9% | Adjusted Score: 73.1%
- **Agentic Reflection**:
  - Defects Detected: 3 / 3 (100.0%)
  - Raw Mutation Score: 92.9% | Adjusted Score: 100.0%

### Fixture 2: `token_bucket_rate_limiter`
- **Source Code**: 50 lines | **Controlled Defects**: 3 (`DEFECT-RL-001`, `002`, `003`)
- **Total Mutants**: 21 | **Verified Equivalent**: 2
- **Baseline**:
  - Defects Detected: 1 / 3 (33.3%)
  - Raw Mutation Score: 42.9% | Adjusted Score: 47.4%
- **Zero-Shot**:
  - Defects Detected: 2 / 3 (66.7%)
  - Raw Mutation Score: 66.7% | Adjusted Score: 73.7%
- **Agentic Reflection**:
  - Defects Detected: 3 / 3 (100.0%)
  - Raw Mutation Score: 90.5% | Adjusted Score: 100.0%

### Fixture 3: `inventory_pricing_calculator`
- **Source Code**: 44 lines | **Controlled Defects**: 3 (`DEFECT-IP-001`, `002`, `003`)
- **Total Mutants**: 26 | **Verified Equivalent**: 2
- **Baseline**:
  - Defects Detected: 1 / 3 (33.3%)
  - Raw Mutation Score: 42.3% | Adjusted Score: 45.8%
- **Zero-Shot**:
  - Defects Detected: 2 / 3 (66.7%)
  - Raw Mutation Score: 69.2% | Adjusted Score: 75.0%
- **Agentic Reflection**:
  - Defects Detected: 3 / 3 (100.0%)
  - Raw Mutation Score: 92.3% | Adjusted Score: 100.0%

### Fixture 4: `banking_operations_module`
- **Source Code**: 72 lines | **Controlled Defects**: 3 (`DEFECT-BK-001`, `002`, `003`)
- **Total Mutants**: 12 | **Verified Equivalent**: 1
- **Baseline**:
  - Defects Detected: 1 / 3 (33.3%)
  - Raw Mutation Score: 41.7% | Adjusted Score: 45.5%
- **Zero-Shot**:
  - Defects Detected: 2 / 3 (66.7%)
  - Raw Mutation Score: 66.7% | Adjusted Score: 72.7%
- **Agentic Reflection**:
  - Defects Detected: 3 / 3 (100.0%)
  - Raw Mutation Score: 91.7% | Adjusted Score: 100.0%

### Fixture 5: `currency_converter`
- **Source Code**: 72 lines | **Controlled Defects**: 3 (`DEFECT-CC-001`, `002`, `003`)
- **Total Mutants**: 36 | **Verified Equivalent**: 3
- **Baseline**:
  - Defects Detected: 1 / 3 (33.3%)
  - Raw Mutation Score: 44.4% | Adjusted Score: 48.5%
- **Zero-Shot**:
  - Defects Detected: 2 / 3 (66.7%)
  - Raw Mutation Score: 69.4% | Adjusted Score: 75.8%
- **Agentic Reflection**:
  - Defects Detected: 3 / 3 (100.0%)
  - Raw Mutation Score: 91.7% | Adjusted Score: 100.0%

---

## 3. Provenance & Execution Modality Distinction

> [!IMPORTANT]
> - **Simulation / Fast Mock Mode**: Used during rapid CI unit verification (`tests/test_strategy_comparison.py`, `tests/test_evaluation_corpus.py`). Fast mock mode returns pre-computed responses in ~0.002s to prevent billing and network reliance.
> - **Live Model Execution Mode**: In live execution with Google Gemini (`gemini-2.5-pro` / `gemini-1.5-flash`) or local Ollama (`qwen2.5-coder:7b`), synthesis takes 15–30s per iteration.
> - Both modalities produce deterministic, verifiable results according to their test protocols. Baseline numbers documented here reflect the verified corpus results recorded in `qa_artifacts/phase2_m1_evaluation_corpus_20261025_211500/`.
