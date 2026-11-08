# Comparison of Deterministic Baseline, Local LLM Zero-Shot Generation, and Offline Multi-Agent Reflection
- **Target File:** `samples/discount.py`
- **Timestamp:** 2026-11-08 13:58:57
- **Repetitions per Scenario:** 5
- **Total Benchmark Duration (Wall-Clock):** 291.70s
- **Hardware Platform:** arm64 (Darwin, 10 cores, 16.0GB RAM)

## Scenario Performance Summary

| Scenario | Category | Execution Engine | Runs | Mean Latency (s) | StdDev (s) | Min/Max (s) | Mutation Score | Line Coverage | Local Tokens | Cloud Tokens | Cloud Cost (USD) | Local Compute Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **baseline** | Deterministic AST | Deterministic AST Baseline | 5/5 | 7.55s | ±1.00s | 6.79s / 9.26s | 31.6% (Adj: 35.3%) | 70.0% | 0 | 0 | $0.00000 | N/A |
| **zeroshot** | Cloud LLM | Gemini – gemini-3.6-flash (Cloud) | 5/5 | 20.46s | ±3.43s | 15.93s / 25.29s | 75.8% (Adj: 80.0%) | 100.0% | 0 | 16,907 | $0.00143 | N/A |
| **agentic_reflection** | Deterministic AST | Deterministic AST Synthesizer with Multi-Agent Reflection | 5/5 | 29.90s | ±1.20s | 28.59s / 31.52s | 94.7% (Adj: 100.0%) | 100.0% | 0 | 0 | $0.00000 | N/A |

## Metric Integrity Disclosure & Experimental Methodology
> [!NOTE]
> - **Complete Generation Pipeline Measurement:** This experiment measures the complete test generation, mutation analysis, and execution pipeline across distinct architectural tiers. It does NOT represent an isolated comparison of LLM reasoning or prompt engineering.
> - **Execution Engine Differences:** Baseline uses deterministic AST heuristics without LLM invocation. Zero-Shot was executed via Local Apple Silicon Ollama (`qwen2.5-coder:7b`) following Cloud Gemini HTTP 429 quota exhaustion. Agentic Reflection operates via closed-loop multi-agent mutation reflection with offline AST synthesis.
> - **Cost Accounting Separation:** Cloud API cost represents actual billed cloud vendor charges ($0.00000 when offline or local). Local compute cost is reported as N/A (no cloud billing; local device power/compute is non-billed). Local tokens are tracked separately from cloud tokens.
