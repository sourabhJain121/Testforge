# Benchmark Validity & Metric Disclosure Audit

**Audit Directory:** `qa_artifacts/autonomous_repair_20261027_112700/`  
**Repository:** `/Users/sourabh/TestForge`  
**Reference Files:** [`benchmark_results.json`](file:///Users/sourabh/TestForge/benchmark_results.json), [`benchmark_results.md`](file:///Users/sourabh/TestForge/benchmark_results.md)

---

## 1. Benchmark Execution Mode & Repetition Audit

In accordance with Part 5 Requirement 10, benchmark artifacts must clearly disclose:
- Actual execution mode (Offline deterministic bridge vs. Live Cloud GenAI).
- Number of repetitions per scenario.
- Measured vs. estimated metrics.
- Exclusions and absence of unearned statistical significance claims.

### Audit Findings:
1. **Repetitions:** `benchmark_results.md` honestly reports:
   `- Repetitions per Scenario: 1`
   The report avoids unearned multi-run statistical variance claims ($\pm 0.00\text{s}$ correctly indicates a single-run measurement, not zero variance).
2. **Execution Engine:** Evaluated using offline deterministic AST mutation and deterministic LLM bridge synthesis (`testforge/crew_critic.py` and `testforge/adk_generator.py`).
3. **Token & Cost Reporting:**
   - Total Tokens: `0` (reflects offline local synthesis).
   - Est. Cost: `$0.00000` (computed from published Google Gemini rates: $0.075/1M prompt, $0.30/1M completion).

---

## 2. Metric Integrity Disclosure

The benchmark report includes the following disclosure banner:

> [!NOTE]
> - **Measured values:** Execution latency, mutant kill counts, and exact token counts are captured directly from OS execution and API telemetry.
> - **Calculated values:** Mutation scores and coverage percentages are computed deterministically via AST analysis.
> - **Estimated values:** Model financial cost in USD is calculated from published pricing rates ($0.075/1M prompt, $0.30/1M completion) and is explicitly flagged as estimated.

---

## 3. Parity Between JSON and Markdown

- In `benchmark_results.json`:
  ```json
  "runs_completed": 1,
  "runs_requested": 1,
  "mean_latency": 1.11,
  "mean_mutation_score": 0.0,
  "line_coverage": 10.0,
  "total_tokens": 0,
  "estimated_cost_usd": 0.0
  ```
- In `benchmark_results.md`:
  Values match the raw JSON data without discrepancies or rounding contradictions.
