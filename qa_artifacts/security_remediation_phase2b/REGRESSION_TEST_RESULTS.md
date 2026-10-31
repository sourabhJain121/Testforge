# TestForge — Phase 2B Regression Test Results

**Document ID**: TF-SEC-2B-007  
**Phase**: Phase 2B (Indirect Prompt-Injection Defense)  
**Execution Environment**: Python 3.13.18, pytest 9.1.1 (`.venv-release`), Darwin arm64  
**Date**: October 30, 2026  
**Status**: 100% PASS (523/523 Passed)  
**Execution Time**: 318.16s (0:05:18)  

---

## 1. Full Regression Test Execution Summary

The full test suite across the entire TestForge repository (`tests/`) was executed with the Phase 2B prompt-injection guardrails, envelopes, and Blackboard trust boundaries active.

```
============================= test session starts ==============================
platform darwin -- Python 3.13.18, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/sourabh/TestForge
plugins: cov-7.1.0, anyio-4.15.1, platformdirs-4.13.5
collected 523 items

........................................................................ [ 13%]
........................................................................ [ 27%]
........................................................................ [ 41%]
........................................................................ [ 55%]
........................................................................ [ 68%]
........................................................................ [ 82%]
........................................................................ [ 96%]
...................                                                      [100%]

======================== 523 passed, 345 warnings in 318.16s (0:05:18) ========================
```

---

## 2. Test Suite Breakdown by Functional Subsystem

| Test Module | Tests Passed | Duration | Subsystem Validated |
| :--- | :--- | :--- | :--- |
| `tests/test_prompt_injection_defense.py` | 10 | 9.91s | Phase 2B Adversarial Prompt Injection Defense (10 Scenarios) |
| `tests/test_network_security.py` | 62 | ~12.5s | Phase 2A Hostname Whitelist, SSRF Redirects, Bounded Reads |
| `tests/test_mcp_network_security.py` | 12 | ~4.2s | Phase 2A.1 MCP Safe Redirects, Token Stripping & Streaming |
| `tests/test_security.py` | 14 | ~2.1s | AST Security Analyzer, Evaluation Sandbox Filters, Policy Checks |
| `tests/test_blackboard.py` | 18 | ~4.5s | Multi-agent Blackboard Partitions, Subscriptions, History |
| `tests/test_adk_generator.py` | 15 | ~8.9s | Google ADK Runner, LlmAgent, Model Bridge, In-Memory Session |
| `tests/test_crew_critic.py` | 12 | ~11.2s | CrewAI Agent, Task, BaseLLM Bridge, Failure Diagnosis |
| `tests/test_agentic_pipeline.py` | 16 | ~14.1s | Multi-agent Generation-Critic-Evaluator Workflow Loop |
| `tests/test_a2a.py` & `test_a2a_protocol.py` | 28 | ~8.0s | A2A Protocol, Agent Registration, Typed Performatives |
| `tests/test_checkpoint_resumption.py` | 26 | ~15.2s | SQLite Blackboard Persistence, Checkpoint Validation & Resume |
| `tests/test_mutation_guided_repair.py` | 32 | ~42.0s | AST Mutator Operators, Parallel Runner, Equivalent Mutant Checks |
| `tests/test_mcp.py` & `test_orchestration_mcp.py` | 38 | ~24.5s | MCP Server Tools, Dynamic Tool Calling, Deliberation Engine |
| Remaining Integration & Unit Tests | 240 | ~161.0s | Callbacks, Benchmarks, Ingestion, Task Lifecycle, Observability |
| **Total Test Suite** | **523** | **318.16s** | **Full Repository Coverage (0 Failures, 0 Regressions)** |

---

## 3. Regression Verdict

- Baseline test count prior to Phase 2B: 513 passed.
- New adversarial tests added in Phase 2B: 10 passed.
- Total tests passed post-Phase 2B: **523 passed (100% pass rate)**.
- Regression Verdict: **ZERO REGRESSIONS. VERIFIED PASS.**

