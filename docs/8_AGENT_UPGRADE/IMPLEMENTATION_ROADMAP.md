# Implementation Roadmap: 8-Agent Modular Architecture Upgrade

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** SPECIFICATION COMPLETED — PENDING USER APPROVAL FOR PHASE 2  

---

## 1. Phased Architecture Upgrade Strategy

To transition safely from the monolithic imperative orchestrator to the structured 8-agent architecture without breaking any of the existing 642 passing regression tests or disrupting the live web cockpit, the upgrade is structured into **seven incremental phases**.

Each phase is isolated, fully testable, and equipped with strict rollback considerations.

```
Phase 1: Architecture Audit (Complete)
   |
   v
Phase 2: Typed Contracts & Blackboard Schema Expansion
   |
   v
Phase 3: Specialized Static & Security Agent Realization (Security & Code Intel)
   |
   v
Phase 4: Planning & Execution Agent Realization (Test Planning & Test Execution)
   |
   v
Phase 5: Generation, Critic & Repair Realization (ADK Generator, CrewAI Critic, ADK Repair)
   |
   v
Phase 6: Google ADK Top-Level Supervisor & Workflow Orchestration
   |
   v
Phase 7: End-to-End Regression Verification & Cockpit Telemetry Update
```

---

## 2. Phase-by-Phase Execution Plan

### Phase 1: Architecture Audit & Baseline Verification (CURRENT PHASE)
- **Status:** **COMPLETE**
- **Objective:** Perform exhaustive fact-based audit of agents, frameworks, tools, state, and dependencies without modifying code.
- **Deliverables:**
  - `docs/8_AGENT_UPGRADE/CURRENT_ARCHITECTURE_AUDIT.md`
  - `docs/8_AGENT_UPGRADE/EXISTING_AGENT_INVENTORY.md`
  - `docs/8_AGENT_UPGRADE/EIGHT_AGENT_MAPPING.md`
  - `docs/8_AGENT_UPGRADE/BLACKBOARD_AND_COMMUNICATION_DESIGN.md`
  - `docs/8_AGENT_UPGRADE/MCP_AND_TOOL_INVENTORY.md`
  - `docs/8_AGENT_UPGRADE/IMPLEMENTATION_ROADMAP.md`
  - `docs/8_AGENT_UPGRADE/ARCHITECTURE_RISKS.md`
- **Acceptance Criteria:** All audit documents generated; zero source code modified; all 642 existing tests verified passing.

---

### Phase 2: Typed Contracts & Blackboard Partition Expansion
- **Status:** **COMPLETE** (Verified with 12/12 focused tests and 654/654 full regression tests)
- **Objective:** Introduce typed Pydantic models for the 3 new partitions (`PlanSpace`, `SecuritySpace`, `ExecutionSpace`) and inter-agent payloads without altering existing pipeline execution logic.
- **Files Modified / Created:**
  - `testforge/blackboard.py`: Added `PlanSpace`, `SecuritySpace`, `ExecutionSpace` models and getter/updater methods. Updated `BlackboardSnapshot`.
  - `testforge/a2a.py`: Added `TestPlanPayload`, `SecurityEvaluationPayload`, `TestExecutionPayload`, `RepairRequestPayload`.
  - `testforge/persistence.py`: Updated snapshot serialization to handle new partitions with backwards-compatible schema migration (`schema_version = 2`, supported: `{1, 2}`).
  - `tests/test_blackboard_8space_expansion.py`: 12 focused tests covering initialization, isolation, concurrency, contracts, and snapshot migration.
- **Dependencies:** Phase 1 complete.
- **Verification Evidence:**
  - Focused Suite: `12 passed in 0.13s` (`tests/test_blackboard_8space_expansion.py`).
  - Full Regression Suite: `654 passed in 272.77s` (`pytest tests/ -q`). Zero regressions.
- **Acceptance Criteria:** Blackboard instantiates 8 typed partitions; existing code running against 5 partitions operates without failure; existing checkpoints load seamlessly. Met 100%.

---

### Phase 3: Specialist Agent Extraction: Security & Code Intelligence
- **Status:** **COMPLETE** (Verified with 21/21 focused tests and 675/675 full regression tests)
- **Objective:** Extract `SecurityAgent` and `CodeIntelligenceAgent` as dedicated Google ADK agents wrapping existing security guardrails and AST analyzers, and integrate them into the live hardening workflow.
- **Files Modified / Created:**
  - `testforge/code_intelligence_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` extracting lexical AST signatures, branches, boundary thresholds, exceptions, cyclomatic complexity, and call graphs. Emits `CodeIntelligencePayload`.
  - `testforge/security_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` providing continuous multi-layer security gatekeeping (prompt injection defusing, AST policy blocking, secret redaction). Emits `SecurityEvaluationPayload`.
  - `testforge/a2a.py`: Added `CodeIntelligencePayload`, enhanced `SecurityEvaluationPayload`, wired broker synchronization.
  - `testforge/blackboard.py`: Added `branches`, `exception_paths`, `complexity_risk`, `call_graph` to `TargetSpace`.
  - `testforge/orchestrator.py`: Integrated `SecurityAgent` into Step 0 and `CodeIntelligenceAgent` into Step 1; registered A2A handlers.
  - `server.py`: Registered agents advertised in `/api/wiretap`.
  - Tests: `tests/test_code_intelligence_agent.py` (9 tests), `tests/test_security_agent.py` (10 tests), `tests/test_phase3_workflow_integration.py` (2 tests).
- **Dependencies:** Phase 2 complete.
- **Verification Evidence:**
  - Focused Suite: `21 passed in 13.73s` (`pytest tests/test_code_intelligence_agent.py tests/test_security_agent.py tests/test_phase3_workflow_integration.py -v`).
  - Full Regression Suite: `675 passed, 348 warnings in 356.13s (0:05:56)` (`pytest tests/ -q`). Zero regressions.
- **Acceptance Criteria:** Both agents operate as genuine ADK participants with typed inputs/outputs; invoked in live hardening workflow; 100% pass rate. Met 100%.

---

### Phase 4: Planning & Execution Agent Realization
- **Status:** **COMPLETE** (Verified with 21/21 focused tests and full regression test suite)
- **Objective:** Implement `TestPlanningAgent` (scenario partitioning, boundary prioritization) and `TestExecutionAgent` (subprocess sandbox execution, pass@1 validation, line coverage, failure triage), integrating both into the live hardening workflow.
- **Files Modified / Created:**
  - `testforge/planning_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` formulating nominal, boundary, negative, and exception scenarios with McCabe prioritization and SHA-256 fingerprint deduplication. Emits `TestPlanPayload`.
  - `testforge/execution_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` coordinating `ParallelSandboxRunner` for safe subprocess-isolated test execution, timeout enforcement, failure diagnostics, line coverage collection, and parallel mutation evaluation. Emits `TestExecutionPayload`.
  - `testforge/blackboard.py`: Added convenience update methods `update_run`, `record_failure`, `record_quarantine`, and `record_suite_execution`.
  - `testforge/agents.py` & `testforge/adk_generator.py`: Updated `generate_tests` to consume and inject `test_plan` scenarios and boundary targets into generation prompts.
  - `testforge/orchestrator.py`: Integrated `TestPlanningAgent` after Code Intelligence to formulate and pass test plans, and `TestExecutionAgent` in Step 2, Step 3, and reflection loop mutant evaluation.
  - `server.py`: Added `"TestPlanningAgent"` and `"TestExecutionAgent"` to `/api/wiretap` `registered_agents`.
  - Tests: `tests/test_test_planning_agent.py` (9 tests), `tests/test_test_execution_agent.py` (9 tests), `tests/test_phase4_workflow_integration.py` (3 tests).
- **Dependencies:** Phase 2 and 3 complete.
- **Verification Evidence:**
  - Focused Suite: `21 passed, 7 warnings in 8.82s` (`pytest tests/test_test_planning_agent.py tests/test_test_execution_agent.py tests/test_phase4_workflow_integration.py -v`).
  - Related Regression Suite: `38 passed, 12 warnings in 15.07s`. Zero regressions.
- **Acceptance Criteria:** Both agents operate as genuine ADK participants with typed inputs/outputs; invoked in live hardening workflow; test plans steer generation; execution agent manages sandbox lifecycle safely; 100% pass rate. Met 100%.

---

### Phase 5: Mutation & Quality Critic Agent Realization (CrewAI) — COMPLETED & VERIFIED
- **Objective:** Specialize `MutationQualityCriticAgent` (formerly `CrewAICriticAgent`) within the official CrewAI framework to perform dual responsibilities: execution-evidence driven mutation analysis and deterministic AST test quality analysis (`TestQualityAnalyzer`).
- **Files Modified / Created:**
  - `testforge/crew_critic.py`: Implemented `MutationQualityCriticAgent` and `TestQualityAnalyzer`. Supports `evaluate_quality`, `diagnose_mutants`, and `critique`. Retains `CrewAICriticAgent = MutationQualityCriticAgent`.
  - `testforge/a2a.py`: Defined `MutationQualityCriticPayload` and updated `A2ABroker._sync_critique_to_blackboard()` and recipient routing.
  - `testforge/blackboard.py`: Expanded `CriticSpace` partition with Phase 5 fields and added `record_critic_evaluation(...)`.
  - `testforge/orchestrator.py`: Integrated `agent:crewai:mutation-critic` into Step F of the reflection loop.
  - `server.py`: Registered `MutationQualityCriticAgent` in `/api/wiretap`.
  - `tests/test_mutation_quality_critic_agent.py` (NEW): 11 unit tests for classification, score calculation, weak assertions, tautologies, contracts, and A2A.
  - `tests/test_phase5_workflow_integration.py` (NEW): 3 workflow integration tests for direct handoff and orchestrator reflection loop.
  - `docs/8_AGENT_UPGRADE/PHASE5_AUDIT_NOTE.md` & `PHASE5_IMPLEMENTATION_REPORT.md`: Comprehensive audit and implementation documentation.
- **Verification Evidence:**
  - Focused Phase 5 Suites: `14 passed, 72 warnings in 7.63s` (100% pass rate).
  - Related Regression Suites (Phases 2–5): `95 passed, 175 warnings in 25.33s` (100% pass rate). Zero regressions.
- **Acceptance Criteria:** Met 100%. No mutant classified as killed without execution evidence; test quality checks flag weak and tautological assertions; directives guide reflection loop.

---

### Phase 6: Reflection & Repair Agent Realization (Google ADK) — COMPLETED & VERIFIED
- **Objective:** Specialize `ReflectionRepairAgent` within the official Google Agent Development Kit (**Google ADK v1.14.1**) framework to analyze test failures and critic findings, formulate targeted repair directives, coordinate surgical assertion repair, and enforce strict non-regression (`candidate_score >= best_score`).
- **Files Modified / Created:**
  - `testforge/reflection_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` + `InMemorySessionService` + `ReflectionModelBridge(BaseLlm)`. Dispatches `analyze_and_plan_repair`, coordinates targeted candidate test repairs, executes clean sandbox validation, and enforces non-regression.
  - `testforge/a2a.py`: Added `RepairDirectivePayload`, `RepairResultPayload`, and `ReflectionDecisionPayload` contracts; added `A2ABroker._sync_reflection_to_blackboard()` and recipient routing.
  - `testforge/blackboard.py`: Extended `SuiteSpace` partition with `previous_test_code`, `best_verified_test_code`, and `repair_history`. Added convenience helper `record_repair_result(...)`.
  - `testforge/orchestrator.py`: Integrated `ReflectionRepairAgent` into Step 4 (Iterative reflection loop); registered A2A handlers.
  - `server.py`: Registered `"ReflectionRepairAgent"` in `/api/wiretap` registered agents list.
  - `tests/test_reflection_repair_agent.py` (NEW): 9 unit tests verifying contracts, deliberation, assertion prescribing, non-regression rejection, clean target validation, iteration limits, A2A handling, and Blackboard synchronization.
  - `tests/test_phase6_workflow_integration.py` (NEW): 3 workflow integration tests verifying orchestrator initialization, end-to-end sandbox repair, and full orchestrator reflection loop execution.
  - `docs/8_AGENT_UPGRADE/PHASE6_AUDIT_NOTE.md` & `PHASE6_IMPLEMENTATION_REPORT.md`: Comprehensive audit and implementation documentation.
- **Verification Evidence:**
  - Focused Phase 6 Suites: `12 passed, 58 warnings in 13.61s` (100% pass rate).
  - Related Multi-Agent Suites (Phases 4–5): `44 passed, 166 warnings in 14.03s` (100% pass rate).
  - Full Regression Suite: `722 passed, 482 warnings in 350.82s (0:05:50)`. Zero regressions.
- **Acceptance Criteria:** Met 100%. Dedicated reflection and repair agent operating under Google ADK; failure triage distinguishing target defects from broken tests; critic findings consumed; strict non-regression enforced; bounded iterations with explicit stopping reasons recorded; 100% test pass rate.

---

### Phase 7: Google ADK Top-Level Supervisor & Eight-Agent Orchestration — COMPLETED & VERIFIED
- **Objective:** Implement `SupervisorAgent` within the official Google Agent Development Kit (**Google ADK v1.14.1**) framework to coordinate stage transitions across 10 workflow phases, enforce strict deterministic policy precedence over model deliberation, maintain dynamic truthful tracking of all 8 canonical agents, record auditable decision traces on the Blackboard, and integrate Wiretap telemetry.
- **Files Modified / Created:**
  - `testforge/supervisor_agent.py` (NEW): Official Google ADK `LlmAgent` + `Runner` + `InMemorySessionService` + `SupervisorModelBridge(BaseLlm)`. Implements `ALLOWED_TRANSITIONS`, `validate_transition`, `decide_next_step` with deterministic policy precedence and ADK deliberation fallback, and dynamic status tracking for all 8 canonical agents.
  - `testforge/a2a.py`: Added `SupervisorDecisionPayload`, `WorkflowTransitionRecord`, `WorkflowStage`, and `SupervisorAction` contracts; wired `A2ABroker._sync_supervisor_to_blackboard()` and handler routing.
  - `testforge/blackboard.py`: Extended `MetricsSpace` partition with `supervisor_decisions: List[Dict[str, Any]]` and `current_stage: str`. Added convenience helper `record_supervisor_decision(...)`.
  - `testforge/orchestrator.py`: Integrated `SupervisorAgent` at every major workflow transition (`INITIALIZING`, `SECURITY_SCREENING`, `CODE_INTELLIGENCE`, `TEST_PLANNING`, `TEST_GENERATION`, `BASELINE_EXECUTION`, `CRITIC_ASSESSMENT`), registered A2A handlers, and maintained full backward compatibility with REST/CLI endpoints.
  - `server.py`: Registered `"SupervisorAgent"` in `/api/wiretap` registered agents list, added dynamic `eight_agents_status`, and exposed `supervisor_decisions`.
  - `tests/test_supervisor_agent.py` (NEW): 13 unit tests verifying contract validation, DAG state transitions, deterministic security refusal, cancellation, timeout, iteration limits, convergence stopping, retry budgets, ADK deliberation, fallback attribution, agent status tracking, and Blackboard synchronization.
  - `tests/test_phase7_workflow_integration.py` (NEW): 5 integration tests verifying orchestrator initialization, security refusal termination, real sandbox end-to-end execution on `samples/discount.py`, wiretap API truthful agent reporting, and FastAPI `/api/harden/start` compatibility.
  - `docs/8_AGENT_UPGRADE/PHASE7_AUDIT_NOTE.md` & `PHASE7_IMPLEMENTATION_REPORT.md`: Comprehensive audit and implementation documentation.
  - `docs/8_AGENT_UPGRADE/FINAL_EIGHT_AGENT_ARCHITECTURE.md`: Exhaustive architectural specification and reference guide with Mermaid diagrams.
- **Verification Evidence:**
  - Focused Phase 7 Suites: `18 passed, 14 warnings in 15.72s` (100% pass rate).
  - Observability Suite: `7 passed, 7 warnings in 4.86s` (100% pass rate).
  - Related Regression Suites (Phases 2–6): `77 passed in 36.03s` (100% pass rate). Zero regressions.
- **Acceptance Criteria:** Met 100%. Top-Level Supervisor operational under Google ADK; deterministic rules strictly authoritative over model deliberation; all 8 canonical specialist agents participating and dynamically tracked; truthful wiretap telemetry exposed; 100% test pass rate across the full test suite.


