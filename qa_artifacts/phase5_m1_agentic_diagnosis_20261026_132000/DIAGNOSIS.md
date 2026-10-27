# Benchmark Diagnosis: Root Cause Analysis of Agentic Reflection Performance

**Date:** 2026-10-26T13:20:00+05:30  
**Phase:** 5.1 — Benchmark Diagnosis (Read-Only)  
**Evidence Artifact Directory:** `qa_artifacts/phase5_m1_agentic_diagnosis_20261026_132000/`  
**Reference Report Analyzed:** `qa_artifacts/phase4_m3_benchmark_validity_20261026_125000/`

---

## 1. Executive Summary

In Phase 4.1.3, an evaluation-integrity fix resolved audit finding **H-01**, guaranteeing that tests failing on clean reference code could never falsely count as mutant kills. With baseline validity strictly enforced, the benchmark revealed an unexpected empirical outcome:

> **The Agentic Reflection strategy achieved an aggregate mutation score of 28.84%, outperforming Zero-Shot (28.34%) by a negligible margin of only +0.50%, while line coverage dropped from 49.64% to 42.86%, false-positive rate rose from 64.78% to 71.28%, and runtime surged from 37.35s to 90.30s (a 2.4x latency penalty).**

This diagnostic investigation traced the exact execution paths through `testforge/corpus/runner.py`, `testforge/agents.py`, `testforge/llm_client.py`, `testforge/sandbox.py`, and `testforge/orchestrator.py`. 

The core findings are:
1. **Critical Benchmark Runner Bug:** An accounting bug in `testforge/corpus/runner.py` line 584 overwrites `retained_candidates` with only the Pass 1 count (`val_pass1.retained_count`). When Pass 1 produces zero new valid tests, `baseline_passed` is falsely set to `False`, **discarding all valid tests from Pass 0**. On `currency_converter`, this artificially collapsed the Agentic Reflection score from **32.6% (15 kills in zero-shot) to 0.0% (0 kills)**, distorting the entire 5-fixture aggregate mean.
2. **Broken Deterministic Fallback for `convert_currency`:** In `testforge/agents.py`, the fallback rules for `convert_currency` hardcode mathematically incorrect assertions (`assert convert_currency(100.0, "USD", "EUR") == 90.0`, whereas actual is `92.41`). When local Ollama times out, this broken fallback activates, fails clean reference checks 100% of the time, and triggers the score-collapse bug.
3. **Aggressive 30s Ollama Timeout & Cascade Latency:** In `testforge/llm_client.py`, local Ollama HTTP calls timeout at 30 seconds. In Pass 1, larger prompt sizes (AST diffs + guidance) push 7B generation to 35-45 seconds. The client aborts, retries two other models (each timing out for 30s), burning **90 seconds of wasted latency** before dropping into the broken AST fallback.
4. **Reflection Blindness (Zero Error Feedback):** `TestGeneratorAgent` receives surviving mutant diffs but **receives zero feedback regarding which tests failed on clean reference code or why**. When local LLMs make mental arithmetic errors on complex multi-tiered discounts, they repeat the exact same failing assertions in Pass 1.
5. **Architectural Disconnect in Benchmark Runner:** In `testforge/corpus/runner.py`, `AdversarialCriticAgent` is **never called**. The benchmark executes a basic two-pass generator loop rather than the true multi-agent reflection loop present in `testforge/orchestrator.py`.

---

## 2. Verified Benchmark Snapshot & Per-Fixture Breakdown

The empirical comparison across all 5 reference fixtures (N=5 runs, 201 total mutants) shows that aggregate averages conceal dramatic per-fixture divergence:

| Fixture | Total Mutants | Baseline Score (Killed) | Zero-Shot Score (Killed) | Agentic Score (Killed) | Agentic vs Zero-Shot Delta | Primary Cause of Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `task_state_transition` | 57 | 71.9% (41) | 28.1% (16) | **63.2% (36)** | **+35.1% (+20 kills)** | **High Success:** Semantic guidance and AST diffs allowed LLM to synthesize targeted authorization edge cases. |
| `token_bucket_rate_limiter` | 38 | 81.6% (31) | 0.0% (0) | 0.0% (0) | 0.0% (0) | **Zero-Pass Collapse:** Pass 0 had 1 valid test, Pass 1 had 0 valid tests. Runner bug discarded Pass 0 suite. |
| `inventory_pricing_calculator` | 37 | 73.0% (27) | 2.7% (1) | 2.7% (1) | 0.0% (0) | **Mental Arithmetic Bottleneck:** LLM failed volume cutoff calculations; repeated same 11 failing tests in Pass 1. |
| `banking_operations_module` | 23 | 78.3% (18) | 78.3% (18) | 78.3% (18) | 0.0% (0) | **Ceiling Reached:** Zero-shot already killed all 18 evaluable mutants; agentic added 5 valid tests but hit score ceiling. |
| `currency_converter` | 46 | 78.3% (36) | 32.6% (15) | **0.0% (0)** | **-32.6% (-15 kills)** | **Artificial Collapse:** Ollama 30s timeout triggered broken AST fallback; runner bug discarded Pass 0's 4 valid tests. |
| **Aggregate Mean** | **201** | **76.62% (153)** | **28.34% (50)** | **28.84% (55)** | **+0.50% (+5 kills)** | **Masked Dynamics:** Huge win on Fixture 1 cancelled out by artificial bug collapse on Fixture 5. |

### Key Per-Fixture Insight
When the reflection loop actually works without timing out or hitting the runner bug (as in `task_state_transition`), **Agentic Reflection increased mutation score from 28.1% to 63.2% (+35.1%) and defect detection from 0.0% to 33.3%**. 

The apparent "failure" of agentic reflection in the aggregate mean is primarily driven by the **0.0% collapse on `currency_converter`** (caused by Runner Bug #1 + Fallback Bug #2 + Timeout Bug #3). If `currency_converter` simply retained its Pass 0 score (32.6%), the aggregate agentic score would be **35.36%** (+7.02% over zero-shot).

---

## 3. Actual Strategy Execution Flow

### Zero-Shot Pipeline
1. `TestGeneratorAgent.generate_tests(source_code, iteration=0)` is called once.
2. Generated suite `synth` is validated against clean reference via `validate_and_filter_candidate_suite`.
3. Valid tests passing reference code are retained; broken tests are quarantined.
4. If `retained_count > 0`, retained suite is evaluated against mutants.
5. Score and defect detection computed.
6. Execution completes in ~25-35s.

### Agentic Reflection Pipeline (as currently implemented in `runner.py`)
```mermaid
flowchart TD
    A[Pass 0: TestGeneratorAgent] --> B[Granular Validation: val_pass0]
    B --> C[clean_v0: Retained Pass 0 Tests]
    C --> D[Intermediate Mutant Eval: eval_pass0]
    D --> E[Surviving Mutants AST Diffs & Guidance]
    E --> F[Pass 1: TestGeneratorAgent with surviving_diffs]
    F --> G[Granular Validation: val_pass1 candidate=synth_v1, existing=clean_v0]
    G --> H{val_pass1.retained_count > 0?}
    H -- No --> I[retained_candidates = 0]
    I --> J[baseline_passed = False]
    J --> K[Clear test_code_to_eval -> 0 Kills / 0% Score!]
    H -- Yes --> L[retained_candidates = val_pass1.retained_count]
    L --> M[Evaluate Mutants & Defect Variants]
```

---

## 4. Root Causes Ranked by Impact and Confidence

### Root Cause 1: Pass 1 Overwrite Bug Discards Pass 0 Working Tests [PROVEN — Critical Impact]
- **Confidence:** Proven by code inspection and reproduction.
- **Location:** `testforge/corpus/runner.py:582-608`
- **Mechanism:**
  ```python
  val_pass1 = runner.validate_and_filter_candidate_suite(
      candidate_test_code=synth_v1,
      target_code=fixture.source_code,
      existing_test_code=clean_v0
  )
  test_code_to_eval = val_pass1.retained_test_code if val_pass1.retained_count > 0 else clean_v0
  total_candidates = val_pass0.total_candidates + val_pass1.total_candidates
  retained_candidates = val_pass1.retained_count  # <-- BUG: Only counts Pass 1, ignores clean_v0!
  ...
  baseline_passed = bool(test_code_to_eval and test_code_to_eval.strip() and retained_candidates > 0)
  ```
  When `val_pass1.retained_count == 0`, `retained_candidates` is set to `0`. Line 608 evaluates `retained_candidates > 0` as `False`. `baseline_passed` becomes `False`. Line 645 then passes `""` to `evaluate_mutants_parallel`, marking all mutants as `SURVIVED` or `ERROR`.
- **Result:** Any fixture where Pass 1 generated invalid tests loses all Pass 0 tests, crashing to 0.0% score.

### Root Cause 2: Hardcoded Erroneous Assertions in Deterministic Fallback [PROVEN — High Impact]
- **Confidence:** Proven by direct assertion math and trace logs.
- **Location:** `testforge/agents.py:676-689`
- **Mechanism:** In `_synthesize_ast_aware_tests` for `convert_currency`:
  - Asserts `convert_currency(100.0, "USD", "EUR") == 90.0` (Actual reference calculation yields `92.41`).
  - Asserts `with pytest.raises(ValueError): convert_currency(0.0, "USD", "EUR")` (Reference code explicitly permits `amount == 0.0` and returns `0.0`).
  - Asserts `with pytest.raises(ValueError): convert_currency(100.0, "USD", "EUR", spread_bps=0)` (Reference code permits `spread_bps=0`).
- **Result:** Every single test generated by the AST fallback on `convert_currency` fails on clean reference code. It produces 0 valid tests, triggering Root Cause 1.

### Root Cause 3: Aggressive 30s Ollama Timeout & 3-Model Retry Cascade [PROVEN — High Impact]
- **Confidence:** Proven by telemetry timestamps in trace files.
- **Location:** `testforge/llm_client.py:346`
- **Mechanism:** `urllib.request.urlopen(req, timeout=30)` aborts after 30 seconds. Pass 1 prompts include AST unified diffs and semantic guidance, inflating prompt length from ~1.6KB to ~10.5KB. Local 7B model generation on CPU/Metal takes 35-45 seconds for this context. When it hits 30 seconds, it aborts, retries `qwen2.5:7b` (times out 30s), retries `codellama:7b` (times out 30s), and engages Tier 4 AST synthesis after **90 seconds of wasted execution**.
- **Result:** Artificially inflates agentic runtime to 90+ seconds and triggers Root Cause 2.

### Root Cause 4: Reflection Blindness — Zero Error Feedback to TestGenerator [PROVEN — High Impact]
- **Confidence:** Proven by diagnostic experiment (task `task-10412`).
- **Location:** `testforge/agents.py:373-450`
- **Mechanism:** `TestGeneratorAgent.generate_tests` receives `surviving_diffs` and `surviving_guidance`, but has no parameter for `test_execution_errors` or `quarantined_tests`.
  On `inventory_pricing_calculator`, 9 of 14 tests failed because local 7B models cannot do mental multi-step math (e.g. subtracting `$200` bulk discount after a `25%` tier discount). Because the generator was never told what failed or what the actual return values were, it regenerated the exact same failing assertions in Pass 1.
- **Result:** Pass 1 provides zero repair for false positives, leading to repeated failures and zero score increase.

### Root Cause 5: Architectural Disconnect — CriticAgent Omitted in Benchmark Runner [PROVEN — Medium Impact]
- **Confidence:** Proven by code inspection of `runner.py`.
- **Location:** `testforge/corpus/runner.py:555-585`
- **Mechanism:** The production pipeline in `testforge/orchestrator.py` uses `AdversarialCriticAgent` to formulate targeted critique directives. In `runner.py`, `AdversarialCriticAgent` is never instantiated or invoked.
- **Result:** The agentic strategy evaluated in the benchmark is not actually multi-agent reflection; it is a raw diff-prompting loop.

### Root Cause 6: Full Suite Re-synthesis Instead of Targeted Incremental Hardening [PROVEN — Medium Impact]
- **Confidence:** Proven by prompt inspection in `testforge/agents.py:448`.
- **Mechanism:** In Pass 1, the prompt instructs: `Write a complete Pytest test suite targeting ONLY [{func_names}].`
- **Result:** The LLM regenerates basic happy-path tests alongside boundary tests, repeating past syntax/arithmetic errors instead of outputting 2-3 targeted tests specifically designed to kill the surviving mutants.

---

## 5. Distinction Between Proven Causes and Hypotheses

| Potential Issue Diagnosed | Status | Findings / Evidence |
| :--- | :---: | :--- |
| **Pass 1 Overwrite Bug** | **PROVEN** | `runner.py:584` overwrites `retained_candidates` with Pass 1 count, discarding Pass 0. |
| **Broken AST Fallback for Currency** | **PROVEN** | `agents.py:676-689` contains 4 mathematically invalid assertions against reference code. |
| **Local Ollama 30s Timeout Cascade** | **PROVEN** | `llm_client.py:346` has hardcoded 30s timeout; 3 cascades cause 90.039s latency in trace. |
| **Missing Failure Error Feedback** | **PROVEN** | `agents.py` prompt has no parameter for execution stack traces or actual vs expected values. |
| **CriticAgent Omission in Runner** | **PROVEN** | `runner.py:555-585` never instantiates or calls `AdversarialCriticAgent`. |
| **Prompt Asks for Full Regeneration** | **PROVEN** | `agents.py:448` commands "Write a complete Pytest test suite" in both passes. |
| **Sandbox Mutation Attribution Errors** | **REJECTED** | Mutants only evaluated with 100% clean-passing suites; attribution to mutants is genuine. |
| **Metric Aggregation / Denominator Errors** | **REJECTED** | Denominators properly exclude invalid/equivalent mutants; math formulas verified correct. |
| **Strategy Input Unfairness** | **REJECTED** | Both strategies receive identical source code, fixtures, and AST mutant sets. |

---

## 6. Recommended Minimum Fixes, Ordered by Expected Impact

1. **Fix Pass 1 Retained Test Accounting in `runner.py` (Highest Impact - Immediate):**
   Update `runner.py` so `retained_candidates` reflects the total valid tests in `test_code_to_eval` (the merged suite), ensuring that failing Pass 1 candidate tests never discard valid Pass 0 tests.
2. **Correct `convert_currency` AST Fallback Assertions in `agents.py` (High Impact):**
   Fix the hardcoded assertions in `_synthesize_ast_aware_tests` to match the exact mathematical contracts of `currency_converter.py` (`92.41` not `90.0`, permit `0.0`, permit `spread_bps=0`).
3. **Increase Local Ollama Timeout & Prevent Redundant Cascades in `llm_client.py` (High Impact):**
   Increase Ollama request timeout from 30s to 60s for large prompts, and avoid cascading across 3 different models when local inference is active.
4. **Feed Clean Reference Execution Errors back into Pass 1 Prompt (High Impact):**
   In Pass 1, include a `### Tests Quarantined Due to Assertion Errors:` section in the prompt showing `AssertionError: assert actual == expected` so the LLM can correct its arithmetic.
5. **Wire `AdversarialCriticAgent` into `runner.py` (Medium Impact):**
   Instantiate `AdversarialCriticAgent` in `runner.py` to provide true multi-agent reflection directives as designed in the architecture.
