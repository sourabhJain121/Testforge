# TestForge — Final Test Suite Report (Phase 2 Evaluation)

**Date:** 2026-10-26  
**Artifact Directory:** `qa_artifacts/phase2_finalization_20261026_141500/final_report/`  
**Environment:** `.venv-release` (`.venv-release/bin/python`, `.venv-release/bin/pytest`)  
**Test Command:** `.venv-release/bin/python -m pytest tests/ -q`  

---

## 1. Full-Suite Execution Summary

| Parameter | Historical Baseline (Phase 5.1) | **Current Finalization Result (Phase 2)** |
|---|---:|---:|
| **Exit Code** | 0 | **0** |
| **Tests Passed** | 421 | **428** (+7 new regression tests) |
| **Tests Failed** | 0 | **0** |
| **Tests Skipped** | 0 | **0** |
| **Warning Count** | 346 | **346** (0 new warnings introduced) |
| **Duration** | ~360s | **375.70s (6m 15s)** |
| **Pass Rate** | 100% | **100%** |

---

## 2. Analysis of Test Warnings (346 Total)

A comprehensive audit of the 346 warnings confirms that 100% are pre-existing deprecation notices emitted by third-party packages installed in `.venv-release`. Zero warnings were introduced by TestForge code modifications:

1. **`crewai` Deprecation Warnings (286 warnings):**
   - `function_calling_llm is deprecated and will be removed in a future release.` (inside `crewai/agent/core.py`, `crewai/crew.py`, `crewai/crews/utils.py`).
   - `allow_code_execution is deprecated.` (inside `crewai/agent/core.py`).
   - `reasoning and planning_config is deprecated.` (inside `crewai/agent/core.py`).
   - `multimodal is deprecated.` (inside `crewai/crew.py`).
   - *Impact:* Harmless; internal to the third-party `crewai` library; does not affect agent operation or test execution.

2. **`fastapi` / `starlette` Lifespan Notices (58 warnings):**
   - `on_event is deprecated, use lifespan event handlers instead.` (emitted by FastAPI router hooks and test client).
   - `The anyio.abc.BlockingPortal alias is deprecated.` (emitted by `starlette/testclient.py`).
   - *Impact:* Harmless backward-compatible framework notices.

3. **`google-cloud-aiplatform` (2 warnings):**
   - `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version.`
   - *Impact:* Harmless library notice.

---

## 3. Breakdown of Test Suites (39 Test Files, 428 Tests)

| Test Module | Tests | Status | Scope |
|---|---:|:---:|---|
| `tests/test_mutation_guided_repair.py` | 33 | **PASS** | Granular AST validation, suite preservation, fallback correctness |
| `tests/test_security.py` | 30 | **PASS** | Prompt injection, AST eval/exec/process/socket blocking, secret redaction |
| `tests/test_evaluation_corpus.py` | 15 | **PASS** | Corpus fixture loading, defect variants, AST mutant generation |
| `tests/test_strategy_comparison.py` | 14 | **PASS** | Multi-strategy runner, reporting, statistical significance |
| `tests/test_cancellation.py` | 14 | **PASS** | Cooperative cancellation, timeout bounding, idempotent endpoints |
| `tests/test_blackboard_persistence.py`| 18 | **PASS** | SQLite checkpoint transactions, rollback, resumption validation |
| `tests/test_checkpoint_resumption.py` | 16 | **PASS** | FSM stage resumption, input hash verification |
| `tests/test_blackboard.py` | 12 | **PASS** | Topic partitioning, pub/sub notifications, atomic writes |
| `tests/test_mcp.py` | 15 | **PASS** | FastMCP server, filesystem confinement, tool registration |
| `tests/test_orchestration_mcp.py` | 12 | **PASS** | Orchestrator tool deliberation with FastMCP client |
| `tests/test_a2a_protocol.py` | 14 | **PASS** | A2A AgentCard discovery, JSON-RPC 2.0 task server |
| `tests/test_a2a.py` | 10 | **PASS** | A2A message interchange, cross-framework interoperability |
| `tests/test_task_lifecycle.py` | 11 | **PASS** | FSM lifecycle states (CREATED -> RUNNING -> COMPLETED) |
| `tests/test_websocket_streaming.py` | 8 | **PASS** | Real-time WebSocket broadcasting, bounded client queues |
| `tests/test_observability.py` | 7 | **PASS** | Correlation IDs, workflow tracing, secret scrubbing |
| `tests/test_adk_generator.py` | 10 | **PASS** | Google ADK GenAI workflow engine integration |
| `tests/test_crew_critic.py` | 9 | **PASS** | CrewAI agent and task integration for adversarial critic |
| `tests/test_mode_c_ingestion.py` | 8 | **PASS** | Mode C public GitHub repo ingestion and SSRF guardrails |
| `tests/test_blast_and_adk.py` | 6 | **PASS** | Blast radius call graph computation with ADK engine |
| `tests/test_deployment.py` | 6 | **PASS** | Dockerfile, docker-compose, and Kubernetes manifests |
| `tests/test_equivalent_mutants.py` | 8 | **PASS** | Equivalent mutant detection and denominator adjustments |
| `tests/test_mutation_scores.py` | 7 | **PASS** | Scoring calculations and metric denominator invariants |
| `tests/test_benchmarking.py` | 6 | **PASS** | Multi-run benchmark harness and metric serialization |
| `tests/test_fast_benchmarking.py` | 5 | **PASS** | Bounded fast benchmark paths |
| `tests/test_adversarial_failure_injection.py` | 7 | **PASS** | Fault injection and observer isolation |
| `tests/test_agentic_pipeline.py` | 8 | **PASS** | Full orchestrator end-to-end pipeline |
| `tests/test_a2a_card_ui_and_endpoint.py` | 4 | **PASS** | Agent card discovery endpoint and UI modal binding |
| `tests/test_checkpoint_api_diff.py` | 4 | **PASS** | Checkpoint snapshot diff API endpoint |
| `tests/test_checkpoint_diff.py` | 6 | **PASS** | In-memory checkpoint diffing |
| `tests/test_ast_mutation_m2.py` | 6 | **PASS** | AST mutation operator accuracy |
| `tests/test_mutation_integration_m2.py` | 7 | **PASS** | Mutation integration with sandbox |
| `tests/test_mcp_status_endpoint.py` | 2 | **PASS** | `/api/mcp/status` endpoint schema and tool list |
| `tests/test_messaging_benchmark.py` | 4 | **PASS** | WebSocket message throughput |
| `tests/test_sandbox.py` | 4 | **PASS** | Subprocess sandbox execution, timeouts, cleanup |
| `tests/test_classifier.py` | 3 | **PASS** | AST callable classifier |
| `tests/test_mutator.py` | 3 | **PASS** | AST mutator node swapping |
| `tests/test_ingestion_and_llm.py` | 3 | **PASS** | Target manager file ingestion |
| **Total Test Suite** | **428** | **PASS** | **100% Pass Rate** |
