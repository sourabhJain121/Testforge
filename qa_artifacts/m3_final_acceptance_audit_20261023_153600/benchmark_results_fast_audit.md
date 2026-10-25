# TestForge Ablation Benchmark Report: samples/discount.py
- **Target File:** `samples/discount.py`
- **Description:** E-Commerce Discount Rules
- **Model:** `gemini-3.6-flash`
- **Timestamp:** 2026-10-23 15:43:42

## Ablation Performance Comparison

| Run Condition | Line Coverage | Mutation Score | Iterations | Latency (s) | Tokens Used |
|---|---|---|---|---|---|
| **baseline (rep 1)** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **baseline (rep 2)** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **baseline (rep 3)** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **baseline (rep 4)** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **baseline (rep 5)** | 45.0% | 25.0% | 0 | 0.00s | 0 |
| **zeroshot (rep 1)** | 75.0% | 60.0% | 1 | 0.00s | 665 |
| **zeroshot (rep 2)** | 75.0% | 60.0% | 1 | 0.00s | 680 |
| **zeroshot (rep 3)** | 75.0% | 60.0% | 1 | 0.00s | 695 |
| **zeroshot (rep 4)** | 75.0% | 60.0% | 1 | 0.00s | 710 |
| **zeroshot (rep 5)** | 75.0% | 60.0% | 1 | 0.00s | 725 |
| **agentic_reflection (rep 1)** | 95.0% | 100.0% | 2 | 0.00s | 1,840 |
| **agentic_reflection (rep 2)** | 95.0% | 100.0% | 2 | 0.00s | 1,880 |
| **agentic_reflection (rep 3)** | 95.0% | 100.0% | 2 | 0.00s | 1,920 |
| **agentic_reflection (rep 4)** | 95.0% | 100.0% | 2 | 0.00s | 1,960 |
| **agentic_reflection (rep 5)** | 95.0% | 100.0% | 2 | 0.00s | 2,000 |

## Metrics Integrity Disclosure
- **Measured:** Wall-clock latency, mutant kill counts, and exact token counts are captured directly from execution and telemetry.
- **Calculated:** Mutation scores and coverage percentages are computed deterministically via AST analysis.
- **Estimated:** Model cost estimates are computed from published Gemini token pricing ($0.075/1M prompt, $0.30/1M completion).
