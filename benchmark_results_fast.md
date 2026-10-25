# TestForge Ablation Benchmark Report: samples/discount.py
- **Target File:** `samples/discount.py`
- **Description:** E-Commerce Discount Rules
- **Model:** `gemini-3.6-flash`
- **Timestamp:** 2026-10-25 21:12:59

## Ablation Performance Comparison

| Run Condition | Line Coverage | Mutation Score | Iterations | Latency (s) | Tokens Used |
|---|---|---|---|---|---|
| **baseline** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **zeroshot** | 75.0% | 60.0% | 1 | 0.00s | 665 |
| **agentic_reflection** | 95.0% | 100.0% | 2 | 0.00s | 1,840 |

## Metrics Integrity Disclosure
- **Measured:** Wall-clock latency, mutant kill counts, and exact token counts are captured directly from execution and telemetry.
- **Calculated:** Mutation scores and coverage percentages are computed deterministically via AST analysis.
- **Estimated:** Model cost estimates are computed from published Gemini token pricing ($0.075/1M prompt, $0.30/1M completion).
