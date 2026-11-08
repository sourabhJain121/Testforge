# TestForge Baselines and External Judge Audit Report

> **Auditor Mode:** Independent Empirical Verification & Methodological Integrity  
> **Evaluation Scope:** `mutmut v3.8.1` external judge, Cloud LLM (Gemini 3.6 Flash / OpenRouter), Local LLM (Ollama `qwen2.5-coder:7b`), and Offline Deterministic Fallbacks  

---

## 1. External Mutation Judge (`mutmut v3.8.1`) Audit

### 1.1. Empirical Run Reproduction
The external judge benchmark was verified via `testforge/scripts/run_external_judge_comparison.py` and `qa_artifacts/EXTERNAL_MUTATION_JUDGE_RESULTS.json`. The external judge was executed across all 4 canonical targets with the following empirical measurements:

| Target Module | mutmut Mutants (Killed / Total) | mutmut Raw Score | TestForge Mutants (Killed / Total) | TestForge Raw Score | TestForge Adj Score | Raw Delta (TF - mutmut) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `discount.py` | 20 / 22 | **90.91%** | 18 / 19 | **94.74%** | **100.0%** | +3.83% |
| `lru_cache.py` | 27 / 85 | **31.76%** | 13 / 42 | **30.95%** | **34.21%** | -0.81% |
| `order_fsm.py` | 97 / 107 | **90.65%** | 103 / 106 | **97.17%** | **97.17%** | +6.52% |
| `stats_calculator.py` | 69 / 136 | **50.74%** | 36 / 73 | **49.32%** | **50.70%** | -1.42% |
| **Macro Average** | **213 / 350** | **66.02%** | **170 / 240** | **68.05%** | **70.52%** | **+2.03%** |

### 1.2. Methodological Findings & Agreement
- **Operator Alignment:** Both tools target comparison operators, boundary inversions, return values, and arithmetic expressions. Both engines exhibit ordinal score parity: `order_fsm.py` (~91-97%) > `discount.py` (~91-95%) > `stats_calculator.py` (~49-51%) > `lru_cache.py` (~31-32%).
- **Equivalence Gap:** `mutmut` lacks an equivalence classifier and treats semantically equivalent mutants (e.g. `price <= 0.0` mutated to `price < 0.0` in `discount.py`) as survived, deflating its raw score to 90.91%, whereas TestForge identifies the invariant equivalence and reaches 100.0% adjusted score.

### 1.3. Statistical Caveat on Pearson Correlation Claim ($r = 0.9988$)
> [!CAUTION]
> **Statistical Significance Limitation ($N=4$):**
> Earlier documentation cited a Pearson correlation coefficient of $r = 0.9988$ ($p = 0.0012$) between TestForge and mutmut. 
> While the numerical calculation across the 4 paired scores `[(90.91, 94.74), (31.76, 30.95), (90.65, 97.17), (50.74, 49.32)]` produces $r = 0.9988$, computing a parametric correlation on only four sample points ($df = 2$) provides minimal statistical power. 
> **Scientific Caveat:** The correlation must be understood as an empirical demonstration of monotonic ordinal agreement across diverse code complexity profiles, not as an asymptotic proof of mathematical identity.

---

## 2. LLM and Deterministic Baseline Provenance Audit

### 2.1. Foundation Models & Execution Environment
TestForge implements a 4-tier hybrid execution cascade (`testforge/llm_client.py`):

1. **Tier 1 (Cloud):** Google GenAI `gemini-3.6-flash` (via official `google-genai` SDK, temperature=0.2). Requires valid `GEMINI_API_KEY`.
2. **Tier 2 (Cloud):** OpenRouter `meta-llama/llama-3.3-70b-instruct` (via OpenAI-compatible chat API, temperature=0.2). Requires `OPENROUTER_API_KEY`.
3. **Tier 3 (Local):** Ollama `qwen2.5-coder:7b` (Q4_K_M quantization, 4,096 token context window, local Apple Silicon Metal GPU acceleration). Zero network egress.
4. **Tier 4 (Offline Fallback):** AST-guided deterministic rule synthesizer (`testforge/intelligent_generator.py`). Zero network calls, zero token consumption, sub-second execution.

### 2.2. Provenance Audit of Baseline Numbers
- **Zero-Shot LLM Benchmarks:** Generated using local Ollama `qwen2.5-coder:7b` with temperature=0.2 and 1-pass generation. Latency averaged 1.66s; token consumption was 2,660 tokens across 4 targets.
- **Deterministic AST Baseline:** In offline test suites (and in test suites run with `CREWAI_TESTING=true`), runs that record 0 tokens utilize the Tier 4 deterministic AST synthesizer. These runs must be explicitly labeled as "Deterministic AST Baseline" rather than LLM generation to maintain scientific honesty.

---

## 3. Audit Remediation Actions
1. Added prominent statistical caveats to `docs/EXTERNAL_MUTATION_JUDGE.md` and `docs/viva/EXAMINER_QA.md` clarifying the $N=4$ sample size limitation on the $r = 0.9988$ claim.
2. Disambiguated offline deterministic AST runs from live LLM invocations across all benchmark summaries.
3. Logged DEF-020 in `docs/DEFECT_LEDGER.md`.

