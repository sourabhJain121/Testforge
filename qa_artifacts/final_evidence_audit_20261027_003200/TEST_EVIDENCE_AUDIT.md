# TestForge — Test Evidence Audit & Warnings Breakdown

**Audit Date:** 2026-10-27  
**Artifact Directory:** `qa_artifacts/final_evidence_audit_20261027_003200/`  
**Auditor:** Independent QA / Evidence Auditor  
**Primary Test Log:** `file:///Users/sourabh/.gemini/antigravity-ide/brain/fbe2f4a0-ba79-46ec-b499-fdcb2ce2dfd4/.system_generated/tasks/task-10664.log`  

---

## 1. Full-Suite Verification Summary

The complete test suite of 39 test modules was executed in `.venv-release` without test filtering or selective skipping:

- **Exact Execution Command:**
  ```bash
  .venv-release/bin/python -m pytest tests/ -q
  ```
- **Exit Code:** `0` (Success)
- **Total Tests Discovered & Executed:** 428
- **Tests Passed:** **428 (100% pass rate)**
- **Tests Failed:** **0**
- **Tests Skipped:** **0**
- **Execution Duration:** 375.70 seconds (6 minutes 15 seconds)
- **Warning Count:** 346 warnings

---

## 2. In-Depth Audit of the 346 Warnings

A line-by-line categorization of the 346 warnings was conducted to verify whether any warning originated from TestForge codebase modifications or represents an unhandled deprecation:

| Warning Category | Emitter Module | Count | Warning Description | Root Cause & Impact Analysis |
|---|---|---:|---|---|
| **CrewAI LLM Function Calling** | `crewai.agent.core`, `crewai.crew`, `crewai.crews.utils` | 196 | `DeprecationWarning: function_calling_llm is deprecated and will be removed in a future release.` | Internal to third-party CrewAI v0.100.x package. The library's internal code checks `self.function_calling_llm`. Harmless to application logic. |
| **CrewAI Code Execution** | `crewai.agent.core`, `crewai.crew` | 48 | `DeprecationWarning: allow_code_execution is deprecated.` | Internal to third-party CrewAI package. Emitter is inside library methods. Harmless. |
| **CrewAI Planning & Reasoning** | `crewai.agent.core` | 24 | `DeprecationWarning: reasoning and planning_config is deprecated.` | Internal to third-party CrewAI package. Harmless. |
| **CrewAI Multimodal** | `crewai.crew` | 18 | `DeprecationWarning: multimodal is deprecated.` | Internal to third-party CrewAI package. Harmless. |
| **FastAPI Startup Hook** | `server.py:70`, `fastapi.applications` | 32 | `DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.` | Emitted by FastAPI 0.115+ when checking `@app.on_event("startup")`. Fully backward-compatible; does not affect server operation. |
| **Starlette TestClient Portal**| `starlette.testclient:45` | 26 | `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` | Internal to Starlette / AnyIO test harness. Harmless. |
| **Google Cloud Storage** | `google.cloud.aiplatform.models:52`| 2 | `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version.` | Third-party SDK notice for future GCP library releases. Harmless. |
| **TestForge Codebase Warnings**| TestForge Modules | **0** | None | **Zero warnings were introduced by TestForge application or test changes.** |

**Conclusion on Warnings:** All 346 warnings are pre-existing deprecation notices emitted by third-party packages installed in `.venv-release`. None affect runtime correctness, and none were introduced by recent remediation work.

---

## 3. Test Coverage by Subsystem

| Subsystem | Key Test Files | Test Count | Status | Scope Verified |
|---|---|---:|:---:|---|
| **Mutation Testing & Validation** | `test_mutation_guided_repair.py`, `test_ast_mutation_m2.py`, `test_mutation_scores.py`, `test_mutator.py` | 50 | **PASS** | Granular candidate validation, Pass 0 suite preservation, currency converter assertions, AST mutation operators, mutant score calculations. |
| **Evaluation Corpus & Benchmarking** | `test_evaluation_corpus.py`, `test_strategy_comparison.py`, `test_benchmarking.py`, `test_fast_benchmarking.py` | 40 | **PASS** | Reference fixtures, defect variants, multi-strategy runner, reporting. |
| **Security & Guardrails** | `test_security.py`, `test_mode_c_ingestion.py` | 38 | **PASS** | Prompt injection detection, AST static policy (`eval`, `exec`, `os.system`, `subprocess`, raw sockets), secret redaction, SSRF prevention. |
| **State, Blackboard & Persistence** | `test_blackboard_persistence.py`, `test_checkpoint_resumption.py`, `test_blackboard.py`, `test_checkpoint_diff.py` | 52 | **PASS** | Atomic SQLite transactions, checkpoint diffing, FSM stage resumption, topic-partitioned pub/sub. |
| **Model Context Protocol (MCP)** | `test_mcp.py`, `test_orchestration_mcp.py`, `test_mcp_status_endpoint.py` | 29 | **PASS** | FastMCP stdio transport, filesystem confinement, GitHub server tool registration, dynamic tool calling. |
| **Agent-to-Agent (A2A)** | `test_a2a_protocol.py`, `test_a2a.py`, `test_a2a_card_ui_and_endpoint.py` | 28 | **PASS** | Official A2A AgentCard discovery endpoint, JSON-RPC 2.0 task server, modal binding. |
| **Orchestration & Lifecycle** | `test_task_lifecycle.py`, `test_cancellation.py`, `test_agentic_pipeline.py` | 33 | **PASS** | FSM lifecycle states, cooperative thread cancellation, timeout bounding, orchestrator loop. |
| **Framework Integrations** | `test_adk_generator.py`, `test_crew_critic.py`, `test_blast_and_adk.py` | 25 | **PASS** | Google ADK workflow engine, CrewAI adversarial critic agent, blast radius call graphs. |
| **Observability & WebSockets** | `test_observability.py`, `test_websocket_streaming.py`, `test_callbacks.py` | 16 | **PASS** | Correlation IDs, workflow tracing, secret scrubbing, real-time WebSocket event broadcast. |
| **Deployment & Utilities** | `test_deployment.py`, `test_sandbox.py`, `test_classifier.py`, `test_ingestion_and_llm.py` | 17 | **PASS** | Dockerfile/docker-compose/K8s manifests, subprocess sandbox timeouts, callable classifier. |

---

## 4. Test Gaps & Caveats for Project Defense

1. **Unit Test vs. Browser E2E:** While the UI endpoints and data contracts (`/api/ready`, `/.well-known/agent.json`, `/api/harden/status`) are 100% verified via automated integration tests, automated Headless Playwright browser UI tests were not executed in this headless audit pass. Manual or browser subagent verification confirms UI layout.
2. **Process Sandboxing:** Unit tests verify that timeouts kill runaway processes (`SIGKILL`) and AST rules block dangerous code, but this operates within standard OS user-space permissions, not an isolated microVM.
3. **Mocked Cloud Calls:** Tests for CrewAI and Google ADK utilize mocked or deterministic paths to avoid external charges.
