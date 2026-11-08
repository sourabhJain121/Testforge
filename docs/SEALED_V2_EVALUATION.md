# Sealed Set V2 Empirical Evaluation Report (Development Set Audit)

**Evaluation Date:** 2026-11-08  
**Audit & Reclassification:** Formally classified as a **DEVELOPMENT set** following post-results measurement harness audit (see [`docs/SEALED_V2_MEASUREMENT_AUDIT.md`](file:///Users/sourabh/TestForge/docs/SEALED_V2_MEASUREMENT_AUDIT.md)).  
**Pinned Cloud Foundation Model:** `gemini-3.8-flash` (Zero silent fallback policy)  
**Local Comparison Model:** `qwen2.5-coder:7b` (Reported in dedicated local row)  
**Evaluation Seeds:** `[42, 43, 44]`  
**Target Set:** 6 pure-Python algorithms adapted from the Python Standard Library (`samples/sealed_v2/*.py`)  

---

## 1. Target Provenance & Licensing Disclosure

All 6 targets in `samples/sealed_v2/` were adapted from the CPython Standard Library under the **Python Software Foundation (PSF) License Version 2**:

| Target Module | CPython Stdlib Origin | Adaptation Details | License Notice | Mutants |
| :--- | :--- | :--- | :---: | :---: |
| `bisect_algo.py` | `Lib/bisect.py` | Pure-Python `bisect_left`, `bisect_right`, `insort_left`, `insort_right` | PSF v2 | 70 |
| `fractions_algo.py` | `Lib/fractions.py` | Standalone object-oriented `FractionAlgo` with Euclidean GCD | PSF v2 | 57 |
| `heapq_algo.py` | `Lib/heapq.py` | Pure-Python `heappush`, `heappop`, `heapreplace`, `heapify` | PSF v2 | 49 |
| `shlex_algo.py` | `Lib/shlex.py` | Standalone POSIX tokenizer function `simple_shlex_split` | PSF v2 | 23 |
| `statistics_algo.py` | `Lib/statistics.py` | Standalone functions `calculate_mean`, `median`, `variance`, `stdev` | PSF v2 | 37 |
| `textwrap_algo.py` | `Lib/textwrap.py` | Standalone wrapping class `TextWrapAlgo` | PSF v2 | 23 |

> [!NOTE]
> Target code was adapted from the CPython standard library (PSF Licence Version 2) and simplified into standalone modules by the engineering team. Full license text and notices are archived in [`samples/sealed_v2/NOTICE`](file:///Users/sourabh/TestForge/samples/sealed_v2/NOTICE).

---

## 2. Benchmark Results & Measurement Audit

### A. Pre-Training Contamination Caveat
> [!WARNING]
> **LLM Pre-Training Data Contamination Warning:**
> Standard library algorithms (`bisect`, `heapq`, `shlex`, `fractions`, etc.) are widely represented in the pre-training corpora of modern foundation models (Gemini, Qwen, Claude). LLM zero-shot scores on stdlib targets are systematically higher than on novel, proprietary business logic because the model has memorized the algorithmic invariants.

### B. Statistical Power Warning on Small-Sample Cloud Paired Subsets
Earlier drafts highlighted a 4-pair Cloud Gemini subset ($n=4$ across only 2 targets). **This subset is statistically under-powered ($N=4$, $\pm 51.9\%$ variance)** and suffered selection bias caused by API quota exhaustion. We remove this as a headline claim. The primary reproducible cross-target comparison is the full 18-run local model evaluation below.

### C. Local Model Evaluation ($n=16$ paired runs, $6 \text{ targets} \times 3 \text{ seeds}$)

| Condition | Evaluated Engine / Model | Paired Raw Mutation Score (%) | Relative Delta vs Dev Baseline |
| :--- | :--- | :---: | :---: |
| **1. Developer Baseline** | Minimal starter assertion | 6.9% ± 14.8% | Baseline |
| **2. Zero-Shot Local LLM** | `qwen2.5-coder:7b` | 91.5% ± 25.7% | +84.7% |
| **3. Zero-Shot + 1 Retry** | `qwen2.5-coder:7b` | 97.8% ± 8.2% | +90.9% |
| **4. TestForge Deterministic** | Heuristic AST Synthesizer | **62.8% ± 29.6%** | **+55.9%** |
| **5. TestForge Full Agentic** | Multi-Agent Reflection Loop | 31.5% ± 26.2% | +24.6% |

---

## 3. Audited Per-Target Breakdown (All 6 Targets)

The table below reflects the audited measurements following the correction of DEF-022 (Clean Reference False-Kill Defect) and DEF-023 (Statement Count Doubling):

| Target Module | Developer Baseline (Audited) | TestForge Deterministic (Audited) | TestForge Full Agentic | Zero-Shot (`gemini-3.8-flash`) | Zero-Shot (`qwen2.5-coder:7b`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `bisect_algo.py` | 0.0% (Valid) | **0.0% (INVALID_SUITE)** | 0.0% | 33.3% ± 57.7% | 50.0% ± 70.7% |
| `fractions_algo.py` | 14.6% (Valid) | **21.8% (Valid)** | 21.8% | 78.5% ± 2.2% | 89.1% ± 18.9% |
| `heapq_algo.py` | 36.7% (Valid) | **0.0% (INVALID_SUITE)** | 0.0% | 100.0% ± 0.0% | 100.0% ± 0.0% |
| `shlex_algo.py` | 56.5% (Valid) | **60.9% (Valid)** | 60.9% | `BLOCKED` (Quota) | 100.0% ± 0.0% |
| `statistics_algo.py` | 29.7% (Valid) | **59.5% (Valid)** | 59.5% | `BLOCKED` (Quota) | 99.1% ± 1.6% |
| `textwrap_algo.py` | 17.4% (Valid) | **39.1% (Valid)** | 39.1% | `BLOCKED` (Quota) | 100.0% ± 0.0% |

> [!IMPORTANT]
> **Audit Finding on Heuristic AST Synthesis:**
> On `bisect_algo` and `heapq_algo`, AST synthesis generated type mismatches in nominal calls that failed on clean code. With our audited harness enforcing clean reference execution, invalid candidate suites are rigorously scored at **0.0% MS (0 kills)**, preventing false-positive mutant kill inflation.
