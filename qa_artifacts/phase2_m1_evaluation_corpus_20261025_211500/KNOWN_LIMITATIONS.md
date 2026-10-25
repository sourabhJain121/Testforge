# TestForge Milestone 2.1 — Known Limitations & Safe Operational Boundaries

## 1. Operational Scope & Boundary Safeguards

This milestone (**Milestone 2.1 / GAP-04**) explicitly bounds its scope to the creation, verification, and deterministic calibration of the **evaluation corpus and benchmark evaluation harness**. The following operational boundaries are enforced:

1. **No Uncalibrated Live LLM Benchmarking Campaigns:**
   - Large-scale multi-run evaluations across commercial LLMs (OpenAI, Anthropic, Google Gemini, OpenRouter) are deferred to **Milestone 2.2 (GAP-05)**.
   - Running massive non-deterministic API campaigns before establishing deterministic baseline ground truth risks burning API quotas and producing uninterpretable metrics.

2. **No Fabricated Token or Cost Metrics:**
   - In offline or simulation environments where API keys (`GEMINI_API_KEY` or `OPENROUTER_API_KEY`) are not provided, token counts and cost metrics are strictly recorded as `0` or labeled `offline_fast_mock`.
   - TestForge strictly prohibits generating synthetic token or financial cost estimates that masquerade as real LLM executions.

3. **Defect Attribution vs Single-Test Failures:**
   - When a defect variant is injected, multiple dependent assertions may fail (e.g., inverting currency cross rates causes multiple currency pair tests to fail). The harness guarantees that the *expected target test* is among the failing assertions; it does not assume that other tests passing or failing is an error.

4. **Equivalent Mutant Classification Limits:**
   - While the mutation framework detects syntactic and trivial semantic equivalence (e.g., dead code mutations, trivial constant changes), undecidability (Rice's Theorem) prevents automated 100% equivalence detection. Mutants classified as "potentially equivalent" require human or formal verification before being permanently excluded from the denominator.

5. **Sandbox Isolation & Concurrency:**
   - In-memory execution using `exec()` is isolated per run with clean globals and sys.modules. However, high-concurrency multi-threaded evaluation in the same process should be managed through isolated sub-processes to avoid sys.stdout / sys.stderr pollution during parallel test runs.

---

## 2. Deferred Items for Milestone 2.2 (GAP-05)

The following activities are explicitly scheduled for **Milestone 2.2**:
- Execution of multi-sample (N=5 to 10 repetitions per fixture per strategy) empirical LLM runs.
- Statistical significance calculations (paired t-tests / Wilcoxon signed-rank tests, Cohen's d effect sizes, 95% confidence intervals).
- Model-family cost-efficiency curves (Mutation Score vs USD Cost vs Latency).
- Prompt engineering ablations comparing zero-shot, few-shot, and iterative critic reflection.
