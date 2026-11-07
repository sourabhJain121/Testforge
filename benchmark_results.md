# Comparison of Deterministic Baseline, Local LLM Zero-Shot Generation, and Offline Multi-Agent Reflection
- **Target File:** `samples/discount.py`
- **Timestamp:** 2026-11-07 15:47:38
- **Repetitions per Scenario:** 1
- **Total Benchmark Duration (Wall-Clock):** 1.56s
- **Hardware Platform:** arm64 (Darwin, 10 cores, 16.0GB RAM)

## Scenario Performance Summary

| Scenario | Category | Execution Engine | Runs | Mean Latency (s) | StdDev (s) | Min/Max (s) | Mutation Score | Line Coverage | Local Tokens | Cloud Tokens | Cloud Cost (USD) | Local Compute Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **baseline** | Deterministic AST | Deterministic AST Baseline | 1/1 | 1.56s | N/A (1 obs) | 1.56s / 1.56s | 31.6% (Adj: 35.3%) | 70.0% | 0 | 0 | $0.00000 | N/A |

## Metric Integrity Disclosure & Experimental Methodology
> [!NOTE]
> - **Complete Generation Pipeline Measurement:** This experiment measures the complete test generation, mutation analysis, and execution pipeline across distinct architectural tiers. It does NOT represent an isolated comparison of LLM reasoning or prompt engineering.
> - **Execution Engine Differences:** Baseline uses deterministic AST heuristics without LLM invocation. Zero-Shot was executed via Local Apple Silicon Ollama (`qwen2.5-coder:7b`) following Cloud Gemini HTTP 429 quota exhaustion. Agentic Reflection operates via closed-loop multi-agent mutation reflection with offline AST synthesis.
> - **Cost Accounting Separation:** Cloud API cost represents actual billed cloud vendor charges ($0.00000 when offline or local). Local compute cost is reported as N/A (no cloud billing; local device power/compute is non-billed). Local tokens are tracked separately from cloud tokens.
