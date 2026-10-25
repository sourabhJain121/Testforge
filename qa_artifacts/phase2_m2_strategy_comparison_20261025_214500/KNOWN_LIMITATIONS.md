# TestForge Milestone 2.2 — Known Limitations & Safe Operational Boundaries

## 1. Operational Scope & Budget Safeguards

1. **Live Cloud API Spend Authorization Policy:**
   - In strict compliance with the Milestone 2.2 objective ("Do not initiate a large or expensive live campaign without explicit user authorization"), no unbudgeted live cloud API calls were made against commercial providers (OpenAI, Anthropic, OpenRouter, Google Cloud).
   - Although `GEMINI_API_KEY` was detected in the environment, executing a full 5-fixture $\times$ 3-strategy $\times$ 3-repetition campaign would consume an estimated 150,000–350,000 tokens ($0.05–$0.25 USD).
   - In accordance with instructions, live evaluation is marked as **BLOCKED pending explicit user spend authorization**, while the reproducible comparison harness was verified through deterministic fast mock and real local engine execution (`qwen2.5-coder:7b`).

2. **Sample Size Limitations & Non-Parametric Caution:**
   - The corpus contains 5 domain fixtures evaluated over 2 repetitions (30 total runs).
   - An $N=5$ or $N=10$ sample is statistically underpowered for asymptotic parametric hypotheses (such as Student's t-tests).
   - Therefore, while paired differences ($\Delta MS$, $\Delta DDR$) are calculated and reported, **no claims of formal statistical significance ($p < 0.05$) are asserted**.

3. **Hallucination & False Positive Overhead in LLM Test Generation:**
   - As observed in empirical execution, single-pass zero-shot models frequently generate tests with false-positive assertions (up to 70% failure on correct code).
   - While agentic reflection reduces false positives via feedback (dropping to 30%), fully eliminating hallucinations without formal contract specifications remains an open challenge in autonomous software testing.

4. **Local Model Compute & Latency Overhead:**
   - Running local LLM inference (e.g. `qwen2.5-coder:7b` via Ollama) on consumer hardware incurs ~30–80 seconds of wall-clock latency per iteration. For rapid CI/CD gates, the deterministic fast mode (`--fast`) remains the recommended pathway.

---

## 2. Proposed Live Campaign Parameters (For Future Authorization)

If the user authorizes a live model evaluation campaign in the future, the proposed parameters are:
- **Model:** `gemini-2.5-flash` or `gemini-1.5-pro`
- **Scope:** 5 evaluation fixtures $\times$ 3 strategies $\times$ 3 repetitions = 45 runs.
- **Estimated Tokens:** ~225,000 tokens total (~160,000 prompt, ~65,000 completion).
- **Estimated Financial Cost:** ~$0.035 USD (under Gemini Flash published rates of $0.075/1M prompt and $0.30/1M completion).
- **Execution Flag:** `python run_benchmark.py --corpus --repetitions 3 --force-live`
