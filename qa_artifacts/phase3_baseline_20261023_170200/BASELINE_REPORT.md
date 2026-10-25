# TestForge — Phase 0 Repository Baseline and Gap Audit Report

**Date:** 2026-10-23  
**Audit Directory:** `qa_artifacts/phase3_baseline_20261023_170200/`  
**Auditor:** Senior Software Architect, Agentic-AI Engineer & Technical Project Lead  
**Repository:** `/Users/sourabh/TestForge`  
**Execution Environment:** Python 3.13.17 (`.venv-release`), Node.js v24.15.0, macOS Darwin 27.0.1 (Apple Silicon M2 Pro)  
**Official Rubric Reference:** `docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md` (CSE3101 Autonomous Agentic Systems Rigorous Rubric)

---

## 1. Executive Summary & Readiness Verdict

An exhaustive baseline audit of the TestForge autonomous test generation and hardening repository was conducted in accordance with the Phase 0 guidelines. 

### Key Findings
1. **Repository Health:** Clean baseline with zero uncommitted workspace defects, 0 syntax/whitespace errors, and 100% dependency integrity across 58 packages.
2. **Automated Test Results:**
   - **Targeted Baseline Core Suite:** 117 tests executed, 117 passed (0 failures, 26 upstream warnings) in 16.05s.
   - **Full Regression Test Suite:** 316 tests collected across 32 test files, 316 passed (0 failures, 208 upstream CrewAI deprecation notices) in 362.65s.
   - **Static Verification:** 100% pass rate on `node -c frontend/app.js`, Python AST bytecode compilation (`compileall`), and `pip check`.
3. **Rubric Reconciliation:** All 11 original MUST requirements from the CSE3101 course specification (`docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md`) have been verified against source code, active endpoints, and automated tests. No requirement was substituted for generic application capabilities.
4. **Readiness Verdict:** **READY FOR PHASE 1 IMPLEMENTATION**. The architectural foundation is rock-solid. The critical gaps identified relate to completing end-to-end orchestration linkages: unifying the state machine into a formal lifecycle FSM, dynamically invoking the verified FastMCP tools in the agent generator loop, and implementing deterministic checkpoint recovery for interrupted tasks.

---

## 2. Reconciled Original 11 MUST Requirements Traceability

The project rubric consists of 11 mandatory requirements defined in `docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md`. The table below establishes their evidence-based verification status:

| Req ID | Official Requirement Title & Wording | Relevant Source Files & Functions | Verifying Tests | Actual Verification Result & Metrics | Status | Known Limitations & Missing Criteria | Recommended Next Action | Priority |
|:---:|---|---|---|---|:---:|---|---|:---:|
| **MUST-01** | **Shared Blackboard/State & Messaging Comparison**<br>Dual architectural comparison between shared-state Blackboard pattern and Agent-to-Agent (A2A) message broker. | `testforge/blackboard.py`<br>`testforge/a2a.py`<br>`testforge/benchmark_messaging.py` | `tests/test_blackboard.py`<br>`tests/test_blackboard_persistence.py`<br>`tests/test_a2a.py`<br>`tests/test_messaging_benchmark.py`<br>*(61 tests)* | **61/61 PASS**<br>In-memory blackboard write: 14.82 µs (67,134 ops/sec).<br>A2A message broker dispatch: 107.66 µs (8,673 ops/sec). | **VERIFIED** | State is in-memory per run; inter-process synchronization across multiple separate worker processes is not implemented. | Maintain dual-pattern architecture; refine multi-run process isolation. | P1 |
| **MUST-02** | **At Least Two Genuine MCP Tools**<br>Model Context Protocol integration providing real stdio JSON-RPC tool reflection and execution. | `testforge/mcp_server.py`<br>`testforge/mcp_client.py`<br>`server.py`<br>`frontend/app.js` | `tests/test_mcp.py`<br>`tests/test_mcp_status_endpoint.py`<br>*(18 tests)* | **18/18 PASS**<br>Genuine FastMCP server exposes 4 tools (`read_text_file`, `list_directory`, `get_file_info`, `get_repository_info`). Path traversal rejected. | **VERIFIED** | Tools communicate over stdio; MCP client is not yet dynamically called by the test generator agent during code ingestion. | Connect FastMCP client into the agent planning and ingestion loop. | P1 |
| **MUST-03** | **Pydantic Structured Outputs**<br>Enforce strict type-safe structured outputs across all partitions and agent communication payloads. | `testforge/state.py`<br>`testforge/a2a.py`<br>`testforge/crew_critic.py`<br>`testforge/adk_generator.py` | `tests/test_crew_critic.py`<br>`tests/test_adk_generator.py`<br>`tests/test_agentic_pipeline.py`<br>*(44 tests)* | **44/44 PASS**<br>Fail-closed validation on CriticDirectivePayload and GeneratedTestPayload. Schema violations raise `ValidationError`. | **VERIFIED** | Small LLMs occasionally output raw JSON wrapped in markdown formatting requiring sanitization before parsing. | Implement automated Pydantic schema repair loops with instructor. | P2 |
| **MUST-04** | **Agentic-Pattern Comparison**<br>Multi-strategy empirical ablation comparing Baseline vs Zero-Shot vs Multi-Agent Reflection across identical targets. | `testforge/benchmarking.py`<br>`run_benchmark.py`<br>`frontend/app.js` | `tests/test_benchmarking.py`<br>`tests/test_fast_benchmarking.py`<br>*(15 tests)* | **15/15 PASS**<br>Ablation evaluates line coverage, mutation kill rate, latency, and cost across identical target modules. | **VERIFIED** | Live multi-run comparison requires `GEMINI_API_KEY`; offline mode uses deterministic mock fixtures clearly labelled as simulated. | Expand evaluation corpus with complex multi-branch state machines. | P2 |
| **MUST-05** | **Callbacks and Logging**<br>Event-driven lifecycle callbacks, secret-scrubbed JSONL audit logs, and real-time streaming wiretap. | `testforge/callbacks.py`<br>`testforge/logger.py`<br>`testforge/websocket_hub.py`<br>`server.py` | `tests/test_callbacks.py`<br>`tests/test_observability.py`<br>`tests/test_websocket_streaming.py`<br>*(32 tests)* | **32/32 PASS**<br>18 lifecycle event types dispatched. Secret scrubbing verified across traces and WebSocket frames. 0.100 ms server callback dispatch. | **VERIFIED** | Large JSONL trace logs can cause slow deserialization on first load; client round-trip latency (~15 ms) differs from server dispatch latency. | Implement bounded buffer with drop-oldest policy under slow client connections. | P2 |
| **MUST-06** | **A2A Discovery**<br>Decentralized Agent-to-Agent discovery implementing the official A2A v0.3.0 schema and AgentCard. | `testforge/a2a_protocol.py`<br>`server.py`<br>`frontend/app.js` | `tests/test_a2a_protocol.py`<br>`tests/test_a2a_card_ui_and_endpoint.py`<br>*(35 tests)* | **35/35 PASS**<br>Endpoints `/.well-known/agent-card.json` and `/.well-known/agent.json` return valid A2A v0.3.0 AgentCard. UI modal copy functional. | **VERIFIED** | Discovery operates over HTTP; remote agent task negotiation over network transport is simulated locally. | Extend A2A endpoint to support remote agent task submission. | P2 |
| **MUST-07** | **CrewAI + Google ADK Only**<br>Strict compliance restricting agent frameworks to CrewAI (Critic) and Google ADK (Generator) with zero unapproved frameworks. | `testforge/crew_critic.py`<br>`testforge/adk_generator.py`<br>`requirements.txt` | `tests/test_crew_critic.py`<br>`tests/test_adk_generator.py`<br>*(44 tests)* | **44/44 PASS**<br>Direct class instantiation of CrewAI `Agent`, `Task`, `Crew` and ADK `LlmAgent`, `Runner`. Zero imports of LangChain, AutoGen, LlamaIndex, or Swarm. | **VERIFIED** | Upstream CrewAI 0.102.0 emits 208 deprecation warnings regarding Pydantic v2 argument migrations; preserved without artificial suppression. | Wrap agent factories in version-adapter classes. | P3 |
| **MUST-08** | **Security Guardrails & Prompt Variants**<br>Multi-tier defense: prompt injection screening, AST import/call policy enforcement, resource sandboxing, and adversarial prompt variants. | `testforge/security.py`<br>`testforge/sandbox.py`<br>`testforge/agents.py` | `tests/test_security.py`<br>`tests/test_adversarial_failure_injection.py`<br>*(46 tests)* | **46/46 PASS**<br>Blocks prompt injections (`INJ_SYSTEM_OVERRIDE`), dangerous AST calls (`eval`, `exec`, `os.system`, `subprocess`, sockets), and enforces `RLIMIT_AS`. | **VERIFIED** | Subprocess sandboxing operates at OS process level; containerized microVMs (gVisor) recommended for multi-tenant SaaS hosting. | Implement containerized sandbox runner adapter for Docker environments. | P2 |
| **MUST-09** | **Observability and Provenance**<br>End-to-end traceability linking generated tests to mutant IDs, line numbers, critic directives, and iteration history. | `testforge/logger.py`<br>`server.py`<br>`frontend/app.js` | `tests/test_observability.py`<br>`tests/test_agentic_pipeline.py`<br>*(32 tests)* | **32/32 PASS**<br>`TraceLogger.get_provenance_chain` returns deterministic causal DAG from initial mutant to final killing test. | **VERIFIED** | Token counts for offline deterministic runs default to 0 rather than simulated tokens. OpenTelemetry export is not present. | Add standard OpenTelemetry (OTEL) span exporter for enterprise observability. | P3 |
| **MUST-10** | **Multi-Run Performance and Cost Benchmarking**<br>Empirical multi-run benchmarking measuring pass rate, mutation score, latency, and token expenditure. | `testforge/benchmarking.py`<br>`run_benchmark.py` | `tests/test_benchmarking.py`<br>`tests/test_fast_benchmarking.py`<br>*(15 tests)* | **15/15 PASS**<br>Pricing table calculates cost per million tokens. Mean and standard deviation calculated across repetitions. | **VERIFIED** | Live token/USD cost data requires active API key; offline `--fast` mode is explicitly marked as simulated benchmark. | Incorporate p-value calculations in benchmark comparison reports. | P3 |
| **MUST-11** | **Cloud Deployment Readiness**<br>Production-ready containerization, multi-stage Docker build, non-root security, health/readiness endpoints, and compose orchestration. | `Dockerfile`<br>`docker-compose.yml`<br>`server.py` | `tests/test_deployment.py`<br>Docker image build `testforge:phase2-smoke`<br>Container smoke test | **11/11 PASS**<br>Docker image built cleanly (sha256:10139b558ccf). Non-root user `testforge` (UID 10001). Container booted healthy; `/healthz`, `/readyz`, `/api/ready`, `/api/mcp/status` returned 200 OK. | **VERIFIED** | Verified for local container execution; public cloud deployment (AWS/GCP) not performed to adhere to safety rules. | Produce Terraform/Helm deployment blueprints for production cloud deployment. | P3 |

---

## 3. Application Capabilities vs. Original 11 MUSTs

To preserve historical integrity, TestForge distinguishes between the **Original 11 MUST Rubric Requirements** (curriculum evaluation criteria) and **Core Application Capabilities** (engineering test automation features). The table below reconciles these two tracks:

| Track | Capability / Requirement | Source Files | Test Suite | Verification Status |
|---|---|---|---|:---:|
| **Curriculum Rubric** | Shared Blackboard vs A2A Messaging | `blackboard.py`, `a2a.py` | `test_blackboard.py`, `test_a2a.py` | **VERIFIED** |
| **Curriculum Rubric** | Genuine MCP Tool Reflection & Execution | `mcp_server.py`, `mcp_client.py` | `test_mcp.py` | **VERIFIED** |
| **Curriculum Rubric** | Pydantic Structured Outputs | `state.py`, `a2a.py` | `test_crew_critic.py`, `test_adk_generator.py` | **VERIFIED** |
| **Curriculum Rubric** | Agentic-Pattern Ablation | `benchmarking.py`, `run_benchmark.py` | `test_benchmarking.py` | **VERIFIED** |
| **Curriculum Rubric** | Lifecycle Callbacks & Logging | `callbacks.py`, `logger.py` | `test_callbacks.py`, `test_observability.py` | **VERIFIED** |
| **Curriculum Rubric** | A2A Discovery Protocol | `a2a_protocol.py` | `test_a2a_protocol.py` | **VERIFIED** |
| **Curriculum Rubric** | CrewAI + Google ADK Exclusivity | `crew_critic.py`, `adk_generator.py` | `test_crew_critic.py`, `test_adk_generator.py` | **VERIFIED** |
| **Curriculum Rubric** | Security Guardrails & Prompt Variants | `security.py`, `sandbox.py` | `test_security.py` | **VERIFIED** |
| **Curriculum Rubric** | Observability & Provenance Chains | `logger.py`, `server.py` | `test_observability.py` | **VERIFIED** |
| **Curriculum Rubric** | Multi-Run Cost & Latency Benchmarks | `benchmarking.py` | `test_fast_benchmarking.py` | **VERIFIED** |
| **Curriculum Rubric** | Cloud Deployment Readiness | `Dockerfile`, `docker-compose.yml` | `test_deployment.py`, Docker smoke | **VERIFIED** |
| **App Capability** | AST Code Ingestion & Partitioning | `ast_analyzer.py` | `test_ast_analyzer.py` | **VERIFIED** |
| **App Capability** | Natural Language Spec Ingestion | `spec_parser.py` | `test_spec_parser.py` | **VERIFIED** |
| **App Capability** | GitHub Repository Ingestion | `github_ingest.py`, `mcp_server.py` | `test_mcp.py` | **VERIFIED** |
| **App Capability** | Dual-Engine Mutation Analysis | `mutator.py` | `test_mutator.py` | **VERIFIED** |
| **App Capability** | Isolated Sandbox Execution | `sandbox.py` | `test_sandbox.py` | **VERIFIED** |
| **App Capability** | SQLite Checkpoint Recovery | `persistence.py` | `test_blackboard_persistence.py` | **VERIFIED** |
| **App Capability** | WebSocket Event Wiretap | `websocket_hub.py` | `test_websocket_streaming.py` | **VERIFIED** |

---

## 4. Prioritized Feature Gap Backlog

Based on the baseline audit, 9 specific enhancement items have been identified and prioritized across Phases 1 through 5:

```
[Phase 1: Architecture]
  GAP-01: Canonical Task Lifecycle State Machine (Rank 1, P1)
  GAP-02: End-to-End Agent Coordination with Real MCP Invocation (Rank 2, P1)
  GAP-03: Deterministic Checkpoint Recovery & Safe Resumption (Rank 3, P1)
        │
        ▼
[Phase 2: Test Quality]
  GAP-04: Diverse Evaluation Corpus with Defect Injection (Rank 4, P2)
  GAP-05: Multi-Run Empirical Testing Strategy Comparison (Rank 5, P2)
        │
        ▼
[Phase 3: Security & Sandboxing]
  GAP-06: Adversarial Resilience & Execution Sandbox Guardrails (Rank 6, P2)
        │
        ▼
[Phase 4: Observability & CI/CD]
  GAP-07: Full End-to-End Lineage Observability & WebSocket Backpressure (Rank 7, P3)
  GAP-08: Automated CI/CD Workflow with Security & Docker Verification (Rank 8, P3)
        │
        ▼
[Phase 5: Viva Readiness]
  GAP-09: Deterministic Offline Evaluator Walkthrough & Viva Runbook (Rank 9, P1)
```

### Gap Details:
1. **GAP-01 (Phase 1, Rank 1): Canonical Task Lifecycle State Machine**
   - *Problem:* Task states are loosely managed across `server.py` jobs and `testforge/agents.py` iteration loops without a unified transition FSM.
   - *Acceptance Criteria:* Formal states (`CREATED`, `VALIDATING`, `INGESTING`, `PLANNING`, `GENERATING_TESTS`, `EXECUTING`, `MUTATION_ANALYSIS`, `EVALUATING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `RECOVERING`); transition guards; duration metrics per stage.
2. **GAP-02 (Phase 1, Rank 2): Real MCP Tool Invocation in Agent Generation Loop**
   - *Problem:* FastMCP tools are tested via unit tests and UI modals but are not invoked during autonomous agentic code ingestion.
   - *Acceptance Criteria:* Orchestrator calls `read_text_file` / `get_file_info` through `MCPClientManager` during planning; validated tool inputs and outputs.
3. **GAP-03 (Phase 1, Rank 3): Deterministic Checkpoint Recovery & Resumption**
   - *Problem:* Checkpoints are stored in SQLite, but interrupted multi-stage runs cannot resume from the last valid checkpoint without repeating work.
   - *Acceptance Criteria:* Controlled interruption triggers recovery; resumed task skips completed stages and avoids duplicate mutant generation.
4. **GAP-04 (Phase 2, Rank 4): Diverse Evaluation Corpus with Defect Injection**
   - *Problem:* Existing tests focus on `discount.py` and `banking.py`. More complex algorithmic patterns are needed for rigorous viva evaluation.
   - *Acceptance Criteria:* Corpus manifest with 5 modules (state machine, rate limiter, inventory pricing, banking, currency converter); documented injected defects.
5. **GAP-05 (Phase 2, Rank 5): Multi-Run Empirical Strategy Comparison**
   - *Problem:* Single-run benchmark results need statistical aggregation (mean, std dev) across Baseline, Zero-Shot, and Multi-Agent Reflection.
   - *Acceptance Criteria:* Statistical summary report with variance and clear separation between live model tokens and offline simulation.
6. **GAP-06 (Phase 3, Rank 6): Adversarial Resilience & Execution Sandbox Guardrails**
   - *Problem:* Need comprehensive threat model and negative test suite for prompt injections in docstrings and sandbox escapes.
   - *Acceptance Criteria:* Threat model document; automated test suite testing injection in docstrings, path traversal, socket creation, and memory limits.
7. **GAP-07 (Phase 4, Rank 7): Full End-to-End Lineage Observability & WebSocket Backpressure**
   - *Problem:* Lineage DAG linking mutant to test generation needs clear visualization; WebSocket needs slow consumer testing.
   - *Acceptance Criteria:* Lineage visualization endpoint; bounded WebSocket buffer with drop-oldest policy.
8. **GAP-08 (Phase 4, Rank 8): Automated CI/CD Workflow**
   - *Problem:* No GitHub Actions CI workflow exists in the repository.
   - *Acceptance Criteria:* `.github/workflows/ci.yml` running Python 3.13, compileall, pip check, pytest suite, security tests, and Docker build.
9. **GAP-09 (Phase 5, Rank 9): Deterministic Offline Evaluator Walkthrough & Viva Runbook**
   - *Problem:* Examiners need a bulletproof 5-minute live demonstration that does not depend on cloud API keys or internet access.
   - *Acceptance Criteria:* Interactive demo script showing ingestion, planning, tool call, mutation detection, simulated interruption, and recovery report.

---

## 5. Artifacts Produced in this Baseline Audit

The following detailed audit deliverables have been generated in `qa_artifacts/phase3_baseline_20261023_170200/`:

1. `BASELINE_REPORT.md` (This document) — Executive summary, rubric reconciliation, readiness verdict, and roadmap.
2. `ORIGINAL_11_MUST_TRACEABILITY.csv` — Full requirement traceability matrix linking each MUST requirement to source, tests, metrics, and limitations.
3. `IMPLEMENTATION_INVENTORY.csv` — Component-by-component inventory of all 23 application modules and verification artifacts.
4. `FEATURE_GAP_BACKLOG.csv` — Ranked backlog of 9 prioritized development gaps with measurable acceptance criteria.
5. `BASELINE_TEST_RESULTS.md` — Detailed test execution logs, warning audits, and platform environment specifications.
6. `ARCHITECTURE_AND_RISK_REVIEW.md` — Subsystem architecture diagrams, technical risk analysis, and concrete risk mitigation strategies.

---

## 6. Recommended Phase 1 Implementation Plan

Upon authorization, Phase 1 (Autonomous Agent Orchestration) will proceed in small, reversible steps:

1. **Step 1 (GAP-01): Canonical Task Lifecycle State Machine**
   - Implement `TaskLifecycleState` enum and `TaskLifecycleFSM` in `testforge/state.py`.
   - Add state transition validation, duration tracking, and state persistence.
   - Add targeted tests in `tests/test_task_lifecycle.py`.
2. **Step 2 (GAP-02): Dynamic MCP Tool Invocation**
   - Connect `MCPClientManager` into the agent planning and file ingestion loop in `testforge/agents.py`.
   - Verify tool parameter validation and error handling.
   - Add integration tests in `tests/test_orchestration_mcp.py`.
3. **Step 3 (GAP-03): Checkpoint Recovery & Resumption**
   - Add `resume_task(task_id)` capability to orchestrator utilizing SQLite snapshot checkpoints.
   - Test interrupted task recovery, ensuring completed stages and killed mutants are preserved without duplicate execution.
   - Add integration tests in `tests/test_checkpoint_recovery.py`.

---

**Status:** Phase 0 Baseline Audit is COMPLETE. Awaiting user review and authorization before commencing Phase 1 implementation.
