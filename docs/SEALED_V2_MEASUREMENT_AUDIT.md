# Sealed Set V2 Evaluation & Measurement Harness Audit

**Audit Date:** 2026-11-08  
**Auditor:** Independent Release Engineer & Evaluation Scientist  
**Scope:** Sealed Set V2 benchmark evaluation across 6 pure-Python algorithms adapted from the Python Standard Library (`samples/sealed_v2/`).

---

## 1. Executive Summary & Critical Harness Findings

During independent audit verification of the Sealed Set V2 results, two critical harness bugs were discovered and resolved:

### A. The Clean-Reference Suite Failure False-Kill Defect (DEF-022)
* **The Defect:** In `testforge/benchmarking.py:BenchmarkRunner.evaluate_suite()`, the evaluator directly invoked `self.sandbox.evaluate_mutants_parallel(test_code, mutants)` where `baseline_passed` defaulted to `True`. The harness failed to verify whether the candidate test suite actually passed against the unmodified clean reference code.
* **The Consequence:** When `IntelligentASTSynthesizer` generated candidate suites for targets like `bisect_algo.py` and `heapq_algo.py`, nominal test calls (e.g. passing scalar integers where lists were expected) threw runtime errors on clean code. Because pytest exited with code 1 (`status == FAIL`) across all mutant executions, the uninstrumented harness counted those clean-code failures as mutant kills, erroneously awarding **70/70 kills (100.0%)** on `bisect_algo` and **45/49 kills (91.8%)** on `heapq_algo`!
* **The Fix:**
  1. `BenchmarkRunner.evaluate_suite()` now enforces a strict `pass@1` baseline pre-flight check against clean reference code.
  2. If the test suite fails on clean reference code, it is formally classified as `INVALID_SUITE` (0 kills, 0.0% mutation score, `baseline_passed=False`, `invalid_suite=True`).
  3. Mutant kills are now granularly classified as `ASSERTION_FAIL` (valid assertion kill) vs `EXCEPTION_FAIL` (runtime target exception kill) vs `TIMEOUT` (infinite loop kill) vs `IMPORT_OR_SYNTAX_ERROR` (uncounted).
  4. Consistency Check: Mutants located on lines not present in `cov_info["executed_lines"]` are classified as `SURVIVED` (`kill_classification="UNCOVERED"`). Unreached lines can never be credited as killed.

### B. Statement Count Doubling via Alias Tracking
* **The Defect:** `sandbox.py:measure_coverage()` passed `--cov=target`, `--cov=samples`, and `--cov={cov_module}`, tracking both `target.py` and alias files in `samples/` created inside temporary execution directories. It then read `cov.json["totals"]`, aggregating statement counts across both files and halving reported line coverage (e.g. 50 statements in `target.py` + 50 statements in `samples/bisect_algo.py` = 100 statements).
* **The Fix:** `measure_coverage()` now parses the specific executed target file entry from `cov.json["files"]`, preserving exact statement denominators and covered line lists.

---

## 2. Re-Scoring Table: Old Buggy Harness vs. Audited Harness

Every figure below is derived directly from raw execution in `docs/AUDIT_EVIDENCE/release/rescore_sealed_v2.json`.

| Target Module | Condition | Old Reported MS (%) | Audited MS (%) | Baseline Clean Suite Status | Killed / Total Mutants |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`bisect_algo`** | Developer Baseline | 0.0% | **0.0%** | PASS (Valid) | 0 / 70 |
| **`bisect_algo`** | Deterministic AST | *100.0% (Fabricated)* | **0.0%** | **FAIL (INVALID_SUITE)** | 0 / 70 |
| **`fractions_algo`** | Developer Baseline | 0.0% (Import Error) | **14.6%** | PASS (Valid) | 8 / 57 |
| **`fractions_algo`** | Deterministic AST | 0.0% | **21.8%** | PASS (Valid) | 12 / 57 |
| **`heapq_algo`** | Developer Baseline | 36.7% | **36.7%** | PASS (Valid) | 18 / 49 |
| **`heapq_algo`** | Deterministic AST | *91.8% (Fabricated)* | **0.0%** | **FAIL (INVALID_SUITE)** | 0 / 49 |
| **`shlex_algo`** | Developer Baseline | 0.0% (Import Error) | **56.5%** | PASS (Valid) | 13 / 23 |
| **`shlex_algo`** | Deterministic AST | 56.5% | **60.9%** | PASS (Valid) | 14 / 23 |
| **`statistics_algo`**| Developer Baseline | 0.0% (Import Error) | **29.7%** | PASS (Valid) | 11 / 37 |
| **`statistics_algo`**| Deterministic AST | 59.5% | **59.5%** | PASS (Valid) | 22 / 37 |
| **`textwrap_algo`**  | Developer Baseline | 0.0% (Import Error) | **17.4%** | PASS (Valid) | 4 / 23 |
| **`textwrap_algo`**  | Deterministic AST | 39.1% | **39.1%** | PASS (Valid) | 9 / 23 |

> [!CAUTION]
> **Key Scientific Finding:**
> On `bisect_algo` and `heapq_algo`, heuristic AST synthesis generated tests that failed against clean code. Under the old harness, clean-code failures were erroneously counted as mutant kills. Under the audited harness, invalid test suites correctly yield **0 kills (0.0% MS)**.

---

## 3. Independent Cross-Check with mutmut (3.8.1)

Evidence file: [`docs/AUDIT_EVIDENCE/release/mutmut_cross_check.txt`](file:///Users/sourabh/TestForge/docs/AUDIT_EVIDENCE/release/mutmut_cross_check.txt)

To independently cross-validate TestForge's mutation engine, we executed `mutmut 3.8.1` on 3 targets using the exact same baseline test suites:

| Target | TestForge ASTMutator Mutants | mutmut 3.8.1 Mutants | TestForge Baseline MS | mutmut Baseline MS | Concordance Analysis |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `samples/discount.py` | 19 | 4 | 0.0% (0/19) | 0.0% (0/4) | **100% Agreement**: Minimal oracle fails to kill arithmetic/discount boundary mutants. |
| `samples/order_fsm.py` | 106 | 54 | 0.0% (0/106) | 0.0% (0/54) | **100% Agreement**: Baseline fails to kill state machine transition guards. |
| `samples/sealed_v2/bisect_algo.py` | 70 | 114 | 0.0% (0/70) | 0.0% (0/114) | **100% Agreement**: Starter bisection tests fail to kill internal loop boundary mutations. |

**Mutation Operator Comparison:**
* **TestForge ASTMutator:** Performs structural AST rewrites: Arithmetic Operator Replacement (AOR), Relational Operator Replacement (ROR), Logical Connector Replacement (LCR), Conditional Operator Inversion (COI), and Statement Deletion (CDL).
* **mutmut:** Operates via text/token manipulation with focused replacement mutations.
* **Finding:** Both frameworks agree that minimal or starter developer tests fail to detect boundary and logical mutations, requiring systematic test generation.

---

## 4. Dataset Reclassification: Sealed Set V2 is a DEVELOPMENT Set

Because the evaluation harness and mutation consistency checks were refined post-results to eliminate false-kill artifacts, **Sealed Set V2 can no longer be classified as a blind, untouched "test/evaluation set"**.

In accordance with rigorous machine learning and empirical software engineering standards:
* **Sealed Set V2 is formally reclassified as a DEVELOPMENT set.**
* The adaptions, baseline errors, and synthesizer behaviors were examined and addressed during development.
* Final evaluation claims must acknowledge this reclassification openly.

---

## 5. Provenance & Attribution Disclosure

All 6 targets in `samples/sealed_v2/` were adapted from the CPython Standard Library under the Python Software Foundation (PSF) License Version 2:
* `bisect_algo.py`: Adapted from CPython `Lib/bisect.py`
* `fractions_algo.py`: Adapted from CPython `Lib/fractions.py`
* `heapq_algo.py`: Adapted from CPython `Lib/heapq.py`
* `shlex_algo.py`: Adapted from CPython `Lib/shlex.py`
* `statistics_algo.py`: Adapted from CPython `Lib/statistics.py`
* `textwrap_algo.py`: Adapted from CPython `Lib/textwrap.py`

The complete license text and adaptation details are archived in [`samples/sealed_v2/NOTICE`](file:///Users/sourabh/TestForge/samples/sealed_v2/NOTICE).
Earlier documentation claiming "0 of 6 authored by agent" is revised to:
> *"Target code adapted from CPython (PSF License Version 2), simplified into standalone modules by the engineering team."*

---

## 6. Caveat on Cloud LLM Paired Evaluations

Earlier reports featured headline claims based on $n=4$ paired Gemini runs across only 2 targets due to API quota depletion.
* **Caveat:** Small-sample paired subsets ($n=4$) carry high variance (±51.9%) and risk selection bias.
* **Local Benchmark:** The local Qwen 2.5-Coder (7B) paired evaluation across all 18 runs ($6 \text{ targets} \times 3 \text{ seeds}$) provides the reproducible, un-skewed reference benchmark.
* **Contamination Warning:** Standard library algorithms (such as `bisect` or `heapq`) may have appeared in the pre-training corpora of large language models, potentially inflating zero-shot performance compared to custom proprietary business logic.
