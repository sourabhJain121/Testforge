# Stage 7: Full System Regression Test Results

**Date of Execution:** 2026-10-30  
**Command:** `.venv-release/bin/python -m pytest tests/ -q`  
**Execution Environment:** macOS Darwin, Python 3.13.18, pytest 9.1.1  
**Total Tests Discovered & Executed:** 523  
**Passed Tests:** 523  
**Failed Tests:** 0  
**Skipped / XFailed:** 0  
**Exit Code:** 0  
**Execution Time:** 208.58 seconds (3 minutes 28 seconds)  

---

## 1. Executive Summary

The entire TestForge regression test suite of **523 tests passed cleanly with 0 failures**.

Every core capability—including AST parsing and blast radius analysis, multi-partition Blackboard synchronization, SQLite checkpoint persistence and rollback, CrewAI critic cycles, Google ADK engine wrappers, FastMCP tool servers, network security filters, and prompt-injection defenses—remains 100% stable and regression-free.

---

## 2. Test Execution Details by Subsystem

| Test File | Focus Area | Result |
|---|---|---|
| `test_a2a.py` & `test_a2a_protocol.py` | A2A Protocol, AgentCard discovery, and agent messaging | **PASSED** |
| `test_a2a_card_ui_and_endpoint.py` | AgentCard UI rendering and endpoint schema | **PASSED** |
| `test_adk_generator.py` & `test_blast_and_adk.py` | Google ADK generator and blast-radius call graph scoping | **PASSED** |
| `test_adversarial_failure_injection.py` | Fault tolerance under simulated network/process failure | **PASSED** |
| `test_agentic_pipeline.py` | End-to-end multi-agent orchestration pipeline | **PASSED** |
| `test_ast_mutation_m2.py` & `test_mutator.py` | AST mutation operators and AST tree transformations | **PASSED** |
| `test_benchmarking.py` & `test_fast_benchmarking.py` | Multi-run evaluation benchmark suites and persistence | **PASSED** |
| `test_blackboard.py` & `test_blackboard_persistence.py` | Blackboard spaces, lock safety, SQLite checkpointing | **PASSED** |
| `test_callbacks.py` | EventType emissions, priority subscriptions, and handlers | **PASSED** |
| `test_cancellation.py` | Job cancellation, state cleanup, and background tasks | **PASSED** |
| `test_checkpoint_api_diff.py` & `test_checkpoint_diff.py` | Checkpoint diffing, rollback, and restoration | **PASSED** |
| `test_checkpoint_resumption.py` | Resumption from SQLite state after process interruption | **PASSED** |
| `test_classifier.py` | Architecture/system profiling and heuristic fallbacks | **PASSED** |
| `test_crew_critic.py` | CrewAI agent critique cycles and deterministic fallback | **PASSED** |
| `test_deployment.py` | Health probes, container endpoints, and startup checks | **PASSED** |
| `test_equivalent_mutants.py` & `test_mutation_scores.py` | Equivalent mutant classification and adjusted score calc | **PASSED** |
| `test_evaluation_corpus.py` | Baseline fixture evaluation and multi-target testing | **PASSED** |
| `test_ingestion_and_llm.py` | AST ingestion, docstring analysis, and LLM clients | **PASSED** |
| `test_mcp.py` & `test_mcp_status_endpoint.py` | FastMCP tool registration, dispatch, and schema | **PASSED** |
| `test_mcp_network_security.py` | MCP tool SSRF defense, redirect limits, and cleanups | **PASSED** |
| `test_messaging_benchmark.py` | Micro-benchmarks for Blackboard & A2A dispatch | **PASSED** |
| `test_mode_c_ingestion.py` | GitHub URL ingestion, raw repo fetching, and parsing | **PASSED** |
| `test_mutation_guided_repair.py` | Multi-iteration test repair based on mutant survivors | **PASSED** |
| `test_mutation_integration_m2.py` | End-to-end mutation workflow integration | **PASSED** |
| `test_network_security.py` | SSRF IP blocking, whitelist, 5MB download limit | **PASSED** |
| `test_observability.py` | Structured trace logging and provenance correlation | **PASSED** |
| `test_orchestration_mcp.py` | Orchestrator coordination with FastMCP tools | **PASSED** |
| `test_prompt_injection_defense.py` | 10 adversarial indirect prompt injection scenarios | **PASSED** |
| `test_sandbox.py` | Subprocess isolation, timeouts, and parallel runner | **PASSED** |
| `test_security.py` | Core security guardrails and threat containment | **PASSED** |
| `test_strategy_comparison.py` | Comparative strategy benchmark metrics | **PASSED** |
| `test_task_lifecycle.py` | Task lifecycle transitions, state machines, and events | **PASSED** |
| `test_teacher_review_improvements.py` | Review feedback verification and enhancements | **PASSED** |
| `test_websocket_streaming.py` | Real-time WebSocket event streaming | **PASSED** |

---

## 3. Warning Categorization and Analysis

During the regression run, 345 warnings were emitted by pytest. All 345 were analyzed and categorized:

1. **CrewAI Upstream Deprecation Warnings (339 occurrences):**  
   - `function_calling_llm is deprecated and will be removed in a future release.`
   - `deprecated: if self.allow_code_execution`
   - `deprecated: if self.reasoning and self.planning_config is None`
   - *Impact:* None. Emitted from internal CrewAI 1.15.28 package code; does not affect runtime stability or test execution.

2. **Google Cloud Storage SDK Warning (1 occurrence):**  
   - `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version of google-cloud-aiplatform.`
   - *Impact:* None. Standard forward-looking SDK warning from Google ADK dependencies.

3. **Pydantic-Settings Lifespan Annotation Warning (2 occurrences):**  
   - `IncompleteFieldDefinitionWarning: Field 'lifespan' has an incomplete definition.`
   - *Impact:* None. Starlette lifespan forward reference inside pydantic-settings.

4. **Starlette BlockingPortal Warning (1 occurrence):**  
   - `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.`
   - *Impact:* None. Upstream test client compatibility shim.

5. **Test Generator Class Pytest Collection Warning (2 occurrences):**  
   - `PytestCollectionWarning: cannot collect test class 'TestGeneratorAgent' because it has a __init__ constructor.`
   - *Impact:* None. Pytest warns that `TestGeneratorAgent` in application code is an agent class rather than a test suite class.

---

## 4. Verdict

**PASS:** The codebase exhibits 100% functional integrity across all 523 automated test cases. No regressions or broken dependencies exist.

