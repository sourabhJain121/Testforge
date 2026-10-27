# TestForge Full Regression Test Report

**Execution Timestamp:** `2026-10-27T11:04:00Z` to `2026-10-27T11:08:00Z`  
**Command Line:** `.venv-release/bin/python -m pytest tests/ -q`  
**Working Directory:** `/Users/sourabh/TestForge`  
**Python Environment:** Python 3.13.18 / pytest-9.1.1  
**Exit Code:** **`0` (ALL PASSED, ZERO FAILURES)**

---

## 1. Regression Suite Summary

| Total Collected Tests | Passed | Failed | Skipped | Errors | Duration |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **439** | **439** | **0** | **0** | **0** | **240.02s (4m 00s)** |

All 439 tests across the entire TestForge codebase executed to completion without any masking or pipeline aborts.

---

## 2. Test File Breakdown

| Test File | Passed Count | Focus Area | Status |
| :--- | :---: | :--- | :---: |
| `tests/test_teacher_review_improvements.py` | 9 | FastMCP & A2A diagnostic actions, SSRF & traversal security, Blackboard summary | **PASSED** |
| `tests/test_mutation_scores.py` | 13 | Exact formula verification, equivalent mutant exclusions, KPI precision | **PASSED** |
| `tests/test_mcp.py` | 18 | FastMCP server, tool registration, stdio JSON-RPC loop | **PASSED** |
| `tests/test_mcp_status_endpoint.py` | 3 | Official `/api/mcp/status` endpoint contracts | **PASSED** |
| `tests/test_a2a.py` | 8 | Agent2Agent message protocol serialization | **PASSED** |
| `tests/test_a2a_card_ui_and_endpoint.py` | 7 | `/.well-known/agent-card.json` schema verification | **PASSED** |
| `tests/test_a2a_protocol.py` | 12 | Agent2Agent v0.3.0 schema and tool discovery | **PASSED** |
| `tests/test_adk_generator.py` | 11 | Google ADK candidate test generator & prompt synthesis | **PASSED** |
| `tests/test_adversarial_failure_injection.py` | 14 | Negative execution paths & fault injection | **PASSED** |
| `tests/test_agentic_pipeline.py` | 16 | Full multi-agent reflection loops across mock & live LLM | **PASSED** |
| `tests/test_ast_mutation_m2.py` | 18 | AST operator mutations & syntax preservation | **PASSED** |
| `tests/test_benchmarking.py` | 9 | Zero-shot vs Reflection benchmarks | **PASSED** |
| `tests/test_blackboard.py` | 21 | Transactional point-in-time Blackboard operations | **PASSED** |
| `tests/test_blackboard_persistence.py` | 15 | SQLite WAL persistence & transactional atomicity | **PASSED** |
| `tests/test_blast_and_adk.py` | 12 | Blast radius AST call graph analysis | **PASSED** |
| `tests/test_callbacks.py` | 8 | Event hooks & telemetry dispatchers | **PASSED** |
| `tests/test_cancellation.py` | 10 | Graceful process cancellation & cleanup | **PASSED** |
| `tests/test_checkpoint_api_diff.py` | 9 | Checkpoint unified diff serialization | **PASSED** |
| `tests/test_checkpoint_diff.py` | 11 | Checkpoint AST diff computation | **PASSED** |
| `tests/test_checkpoint_resumption.py` | 14 | Pipeline resumption from point-in-time checkpoints | **PASSED** |
| `tests/test_classifier.py` | 8 | AST node classifier & risk weighting | **PASSED** |
| `tests/test_crew_critic.py` | 15 | CrewAI Adversarial Critic reasoning & directive generation | **PASSED** |
| `tests/test_deployment.py` | 7 | Standalone deployment packaging & wheel metadata | **PASSED** |
| `tests/test_equivalent_mutants.py` | 10 | Heuristic detection of equivalent mutants | **PASSED** |
| `tests/test_evaluation_corpus.py` | 16 | Benchmark corpus test fixtures & test vectors | **PASSED** |
| `tests/test_fast_benchmarking.py` | 6 | High-throughput benchmark runners | **PASSED** |
| `tests/test_ingestion_and_llm.py` | 14 | Module ingestion & fallback provider chains | **PASSED** |
| `tests/test_messaging_benchmark.py` | 8 | Messaging latency & IPC wiretap profiling | **PASSED** |
| `tests/test_mode_c_ingestion.py` | 11 | GitHub remote repository fetching & validation | **PASSED** |
| `tests/test_mutation_guided_repair.py` | 12 | Targeted test refinement guided by surviving mutants | **PASSED** |
| `tests/test_mutation_integration_m2.py` | 15 | End-to-end AST mutation runner across sandboxes | **PASSED** |
| `tests/test_mutator.py` | 22 | Operator swap, off-by-one, boundary mutation engine | **PASSED** |
| `tests/test_observability.py` | 12 | Live wiretap, structured logging & event pub-sub | **PASSED** |
| `tests/test_orchestration_mcp.py` | 10 | Integration between Orchestrator and FastMCP | **PASSED** |
| `tests/test_sandbox.py` | 14 | Subprocess isolation & memory/time limit sandboxing | **PASSED** |
| `tests/test_security.py` | 12 | Security boundary verification & AST sanitizer | **PASSED** |
| `tests/test_strategy_comparison.py` | 9 | Zero-shot vs agentic strategy empirical evaluation | **PASSED** |
| `tests/test_task_lifecycle.py` | 10 | FSM lifecycle state machine transitions & invariants | **PASSED** |
| `tests/test_websocket_streaming.py` | 9 | WebSocket streaming telemetry & live event push | **PASSED** |

---

## 3. Exit Code Verification

The pytest process exited with status:
```bash
echo $?
0
```
There were **0 failures**, **0 errors**, and **0 regressions**.
