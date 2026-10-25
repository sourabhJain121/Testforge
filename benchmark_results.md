# TestForge Ablation Benchmark Report: samples/discount.py
- **Target File:** `samples/discount.py`
- **Description:** E-Commerce Discount Rules
- **Model:** `gemini-3.6-flash`
- **Timestamp:** 2026-10-25 22:17:37

## Ablation Performance Comparison

| Run Condition | Line Coverage | Mutation Score | Iterations | Latency (s) | Tokens Used |
|---|---|---|---|---|---|
| **Condition A (Baseline Minimal)** | 70.0% | 31.6% | 0 | 1.33s | 0 |
| **Condition B (Zero-Shot Single-Pass)** | 100.0% | 63.2% | 1 | 2.19s | 265 |
| **Condition C (TestForge Full Reflection)** | 10.0% | 100.0% | 3 | 33.62s | 1,410 |

## Metrics Integrity Disclosure
- **Measured:** Wall-clock latency, mutant kill counts, and exact token counts are captured directly from execution and telemetry.
- **Calculated:** Mutation scores and coverage percentages are computed deterministically via AST analysis.
- **Estimated:** Model cost estimates are computed from published Gemini token pricing ($0.075/1M prompt, $0.30/1M completion).
