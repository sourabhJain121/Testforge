# TestForge Benchmark & Ablation Study Report
- **Target File:** `samples/discount.py`
- **Timestamp:** 2026-11-02 16:38:53
- **Repetitions per Scenario:** 5
- **Total Benchmark Duration (Wall-Clock):** 113.44s
- **Hardware Platform:** arm64 (Darwin, 10 cores, 16.0GB RAM)

## Scenario Performance Summary

| Scenario | Runs | Mean Latency (s) | StdDev (s) | Min/Max (s) | Mean Mutation Score | Line Coverage | Total Tokens | Engine | Est. Cost (USD) | Actual Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| **baseline** | 5/5 | 1.19s | ±0.06s | 1.13s / 1.28s | 31.6% | 70.0% | 0 est | Deterministic Baseline | $0.00000 | $0.00000 |
| **zeroshot** | 5/5 | 15.11s | ±1.88s | 12.03s / 16.83s | 100.0% | 100.0% | 24,809 actual | Mixed Execution Engines | $0.00253 | $0.00253 |
| **agentic_reflection** | 5/5 | 6.08s | ±0.18s | 5.85s / 6.31s | 89.5% | 100.0% | 0 est | AST Deterministic Synthesizer (Offline) | $0.00000 | $0.00000 |

## Metric Integrity Disclosure
> [!NOTE]
> - **Measured values:** Execution latency, mutant kill counts, and exact token counts are captured directly from OS execution and API telemetry.
> - **Calculated values:** Mutation scores and coverage percentages are computed deterministically via AST analysis. If no evaluable mutants execute, score is reported as N/A.
> - **Estimated values:** Model financial cost in USD is calculated from published pricing rates ($0.075/1M prompt, $0.30/1M completion) and is explicitly flagged as estimated. Offline deterministic runs incur $0.00 actual billed cost.

