# TestForge Phase 4 Implementation Report: Test Planning and Test Execution Agent Realization

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Implementation Date:** November 5, 2026  
**Auditor / Implementer:** Principal AI Systems Architect & Lead Evaluation Reviewer  
**Phase Status:** COMPLETED & VERIFIED  

---

## Executive Summary

Phase 4 of the 8-Agent Modular Architecture Upgrade has been successfully implemented and verified. Two genuine Google ADK cognitive agents—**`TestPlanningAgent`** and **`TestExecutionAgent`**—have been realized and integrated into the live TestForge hardening workflow.

Key achievements in Phase 4:
1. **Google ADK Test Planning Agent:** Built [`testforge/planning_agent.py`](file:///Users/sourabh/TestForge/testforge/planning_agent.py) with official `google.adk.agents.llm_agent.LlmAgent`, `Runner`, and `BaseLlm` bridge (`PlanningModelBridge`). Consumes `CodeIntelligencePayload` (or AST symbols), discovers target callables, formulates structured nominal, boundary, negative, and exception test scenarios, calculates numeric priorities based on McCabe cyclomatic complexity and blast radius, enforces SHA-256 fingerprint deduplication, and identifies external mock dependencies. Emits strongly-typed `TestPlanPayload` and updates Blackboard `PlanSpace`.
2. **Google ADK Test Execution Agent:** Built [`testforge/execution_agent.py`](file:///Users/sourabh/TestForge/testforge/execution_agent.py) with official `google.adk.agents.llm_agent.LlmAgent`, `Runner`, and `BaseLlm` bridge (`ExecutionModelBridge`). Safely coordinates subprocess test execution in isolated temporary environments via `ParallelSandboxRunner` without in-process untrusted code execution. Enforces strict timeouts (default 5.0s), collects passing/failing/skipped/error counts, extracts structured failure diagnostics with tracebacks, accurately measures line coverage via `pytest-cov`, and coordinates parallel mutant evaluation across CPU cores. Emits strongly-typed `TestExecutionPayload` and updates Blackboard `ExecutionSpace` and `SuiteSpace`.
3. **Genuine Workflow Influence & Integration:** In [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py), `TestPlanningAgent` is invoked immediately after `CodeIntelligenceAgent`, logging structured `AGENT_HANDOFF` events (`SecurityAgent` -> `CodeIntelligenceAgent` -> `TestPlanningAgent` -> `TestGeneratorAgent`). The formulated test plan is passed directly to test generators (`TestGeneratorAgent`, `GoogleADKTestGenerator`), genuinely steering prompt formulation with target scenarios, boundary targets, and negative cases. `TestExecutionAgent` coordinates baseline pass@1 validation, repair re-checks, deterministic AST checks, baseline line coverage measurement, and parallel mutation evaluation.
4. **Authoritative In-Process A2A Protocol:** Registered both agents in `A2ABroker` as `agent:google-adk:test-planner` and `agent:google-adk:test-execution`, handling `plan_tests`, `create_test_plan`, `execute_tests`, and `evaluate_mutants` actions.
5. **Observability & Wiretap Registration:** Registered `"TestPlanningAgent"` and `"TestExecutionAgent"` in `server.py` `/api/wiretap` registered agents list, emitting lifecycle events (`OPERATION_START`, `OPERATION_COMPLETE`) and `AGENT_EXECUTION` audit logs to `TraceLogger`.
6. **Zero-Regression Verification:** Verified through 21 new focused tests (100% pass) and 38 related regression tests across Phases 2, 3, and 4 (100% pass).

---

## 1. Concrete Agent Implementations

### 1.1 TestPlanningAgent ([`testforge/planning_agent.py`](file:///Users/sourabh/TestForge/testforge/planning_agent.py))

- **Framework:** Google Agent Development Kit (ADK v1.14.1):
  - Agent: `LlmAgent(name="test_planning_agent", model=self.model_bridge, output_schema=TestPlanPayload)`
  - Session Service: `InMemorySessionService`
  - Runner: `Runner(agent=self.adk_agent, session_service=self.session_service, app_name="testforge")`
  - Model Bridge: `PlanningModelBridge(BaseLlm)` connecting runner deliberation to deterministic AST scenario planning and optional live Gemini LLM reasoning.
- **Agent ID:** `agent:google-adk:test-planner`
- **Responsibilities & Analysis Capabilities:**
  - **Consumption of Code Intelligence:** Parses `CodeIntelligencePayload`, function signatures, discovered branches, condition predicates, exception paths, and dependency lists.
  - **Nominal Scenario Formulation:** Generates nominal validation scenarios for every discovered function/method signature.
  - **Boundary Scenario Extraction:** Parses comparison conditions (`<`, `<=`, `>`, `>=`, `==`, `!=`) using regular expression threshold discovery to identify boundary values and adjacent neighbor values.
  - **Negative & Zero/Empty Cases:** Targets empty collections, null inputs, 0, and negative numbers.
  - **Explicit Exception Scenarios:** Generates exception test targets matching `ast.Raise` and `ast.Try` blocks.
  - **McCabe Cyclomatic Prioritization:** Assigns numeric priorities (`1` for high-complexity `cyclomatic_complexity >= 4` or boundary conditions, `2` for nominal/negative, `3` for lower priority).
  - **Scenario Deduplication:** Emits 16-character SHA-256 content fingerprints (`hashlib.sha256`) per scenario, rejecting duplicates.
  - **Mock Dependency Detection:** Tags external non-standard packages (`requests`, `urllib3`, `redis`, `boto3`, `aiohttp`, `httpx`, `sqlalchemy`) as isolation/mock requirements while ignoring standard library modules (`os`, `sys`, `math`, `json`, `time`).
- **Contract:** Outputs validated [`TestPlanPayload`](file:///Users/sourabh/TestForge/testforge/a2a.py#L251).
- **Blackboard Updates:** Writes `task_id`, `job_id`, `scenarios`, `boundary_conditions`, `negative_cases`, `mock_dependencies`, `allocated_test_budget`, `strategy_notes`, and `planning_status="PLANNED"` to `PlanSpace`.

### 1.2 TestExecutionAgent ([`testforge/execution_agent.py`](file:///Users/sourabh/TestForge/testforge/execution_agent.py))

- **Framework:** Google Agent Development Kit (ADK v1.14.1):
  - Agent: `LlmAgent(name="test_execution_agent", model=self.model_bridge, output_schema=TestExecutionPayload)`
  - Session Service: `InMemorySessionService`
  - Runner: `Runner(agent=self.adk_agent, session_service=self.session_service, app_name="testforge")`
  - Model Bridge: `ExecutionModelBridge(BaseLlm)` connecting runner deliberation to execution telemetry synthesis.
- **Agent ID:** `agent:google-adk:test-execution`
- **Execution Architecture & Security Guardrails:**
  - **Subprocess Isolation:** Delegates actual pytest and pytest-cov execution to `ParallelSandboxRunner`.
  - **No In-Process Untrusted Execution:** Untrusted candidate test code and mutated source are written to isolated temporary directories (`tempfile.TemporaryDirectory(prefix="testforge_box_")`).
  - **AST Security Policy Pre-Check:** Test code is pre-screened against `SecurityGuardrail` AST policies before subprocess launch.
  - **Strict Timeout Guardrail:** Enforces strict execution timeout (default 5.0s, configurable), killing hangs or infinite loops and returning `status="TIMEOUT"`.
  - **Cancellation Responsiveness:** Checks `cancel_event` before and during execution, exiting cleanly with cancelled telemetry.
  - **Telemetry Extraction:**
    - Parses pytest stdout/stderr to extract individual test outcomes (`test_results`), passed count, failed count, skipped count, and error count.
    - Extracts structured failure blocks with `test_id`, `error_message`, and `traceback`.
    - Measures actual line coverage percentage, covered lines, and statement count via `pytest-cov` without hallucination.
  - **Parallel Mutant Evaluation:** Coordinates concurrent mutation evaluation across CPU worker processes via `ParallelSandboxRunner.evaluate_mutants_parallel`, strictly enforcing baseline qualification before marking mutants `KILLED`.
- **Contract:** Outputs validated [`TestExecutionPayload`](file:///Users/sourabh/TestForge/testforge/a2a.py#L289).
- **Blackboard Updates:**
  - `ExecutionSpace`: updates run telemetry (`update_run`), records failure traces (`record_failure`), records quarantined tests (`record_quarantine`).
  - `SuiteSpace`: updates `baseline_passed`, `baseline_tests_executed`, `baseline_tests_passed`, `baseline_tests_failed`, `baseline_tests_errors` (`record_suite_execution`).

---

## 2. Actual Workflow Integration

In [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py):

1. **Instantiation & Broker Registration (`__init__`):**
   ```python
   from testforge.planning_agent import TestPlanningAgent
   from testforge.execution_agent import TestExecutionAgent
   self.planning_agent = TestPlanningAgent(
       api_key=api_key,
       blackboard=self.blackboard,
       callbacks=self.callbacks,
       logger_instance=self.logger,
   )
   self.execution_agent = TestExecutionAgent(
       sandbox_runner=self.sandbox,
       blackboard=self.blackboard,
       callbacks=self.callbacks,
       logger_instance=self.logger,
       timeout_seconds=self.timeout_seconds,
   )
   self.broker.register_handler("agent:google-adk:test-planner", self.planning_agent.handle_a2a_message, ...)
   self.broker.register_handler("agent:google-adk:test-execution", self.execution_agent.handle_a2a_message, ...)
   ```

2. **Planning Phase (Step 1 Ingestion / Symbol Extraction):**
   - After `CodeIntelligenceAgent.analyze_source()`, `self.planning_agent.plan_tests()` is invoked.
   - Logs `AGENT_HANDOFF` from `CodeIntelligenceAgent` to `TestPlanningAgent`.
   - Stores plan payload in `self.state.metadata["test_plan"]`.
   - Logs `AGENT_HANDOFF` from `TestPlanningAgent` to `TestGeneratorAgent`.

3. **Candidate Synthesis (Step 1 Synthesis):**
   - Formulated test plan is passed to test generators (`generate_tests(..., test_plan=test_plan)`).
   - In [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py) and [`testforge/adk_generator.py`](file:///Users/sourabh/TestForge/testforge/adk_generator.py), planned scenarios, boundary targets, and negative cases are injected directly into generation prompts.

4. **Execution Phase (Step 2 Baseline Validation & Step 3 Coverage):**
   - Coordinates pass@1 validation using `self.execution_agent.execute_tests(..., measure_coverage=False)`.
   - Coordinates self-repair re-checks and deterministic AST validation via `self.execution_agent.execute_tests(...)`.
   - Measures baseline line coverage in Step 3 via `self.execution_agent.execute_tests(..., measure_coverage=True)`.
   - Updates `ExecutionSpace` and `SuiteSpace` partitions atomically on Blackboard.

5. **Mutation Evaluation (Reflection Loop Step C):**
   - Executes parallel mutant evaluation across CPU workers via `self.execution_agent.evaluate_mutants(...)`.

---

## 3. Observability & Telemetry

- **Lifecycle Events Dispatched:** `OPERATION_START` and `OPERATION_COMPLETE` for both `TestPlanningAgent` and `TestExecutionAgent`.
- **Trace Logger Invocations:** Recorded under `AGENT_EXECUTION` and `MUTATION_EVALUATION_COMPLETE` with agent name, framework (`Google ADK`), run IDs, coverage %, and timings.
- **Wiretap Dashboard (`server.py`):** `/api/wiretap` registers both `"TestPlanningAgent"` and `"TestExecutionAgent"` in `registered_agents` and records real-time handoffs.

---

## 4. Test Verification Evidence

### 4.1 Phase 4 Focused Test Suite (21 Tests, 100% Passed in 8.82s)

```
tests/test_test_planning_agent.py::test_planning_agent_instantiation PASSED
tests/test_test_planning_agent.py::test_planning_from_code_intelligence PASSED
tests/test_test_planning_agent.py::test_scenario_prioritization PASSED
tests/test_test_planning_agent.py::test_scenario_deduplication PASSED
tests/test_test_planning_agent.py::test_mock_dependency_detection PASSED
tests/test_test_planning_agent.py::test_blackboard_planspace_sync PASSED
tests/test_test_planning_agent.py::test_a2a_communication_handler PASSED
tests/test_test_planning_agent.py::test_empty_or_malformed_input_handling PASSED
tests/test_test_planning_agent.py::test_lifecycle_events_dispatched PASSED

tests/test_test_execution_agent.py::test_execution_agent_instantiation PASSED
tests/test_test_execution_agent.py::test_clean_tests_execution PASSED
tests/test_test_execution_agent.py::test_failing_assertion_execution PASSED
tests/test_test_execution_agent.py::test_syntax_error_execution PASSED
tests/test_test_execution_agent.py::test_timeout_enforcement PASSED
tests/test_test_execution_agent.py::test_blackboard_execution_space_sync PASSED
tests/test_test_execution_agent.py::test_cancellation_handling PASSED
tests/test_test_execution_agent.py::test_a2a_communication_handler PASSED
tests/test_test_execution_agent.py::test_evaluate_mutants_coordination PASSED

tests/test_phase4_workflow_integration.py::test_orchestrator_initializes_phase4_agents PASSED
tests/test_phase4_workflow_integration.py::test_orchestrator_end_to_end_phase4_workflow PASSED
tests/test_phase4_workflow_integration.py::test_checkpoint_persistence_with_phase4_spaces PASSED

======================== 21 passed, 7 warnings in 8.82s ========================
```

### 4.2 Related Regression Tests (38 Tests, 100% Passed in 15.07s)

```
tests/test_code_intelligence_agent.py (9 tests) PASSED
tests/test_security_agent.py (10 tests) PASSED
tests/test_blackboard_8space_expansion.py (12 tests) PASSED
tests/test_agent_wiretap_integrity.py (5 tests) PASSED
tests/test_phase3_workflow_integration.py (2 tests) PASSED

======================= 38 passed, 12 warnings in 15.07s =======================
```

---

## 5. Scope Boundary Compliance

| Requirement | Status | Notes |
|---|---|---|
| Implement TestPlanningAgent (Google ADK) | COMPLETED | `testforge/planning_agent.py` using official ADK constructs |
| Implement TestExecutionAgent (Google ADK) | COMPLETED | `testforge/execution_agent.py` using official ADK constructs |
| Integrate into TestForgeOrchestrator | COMPLETED | Genuine participation in Step 1, Step 2, Step 3, and loop |
| No in-process untrusted code execution | COMPLETED | Sandboxed subprocess isolation strictly preserved |
| Blackboard PlanSpace & ExecutionSpace sync | COMPLETED | Strongly typed payloads committed to partitions |
| Do NOT implement Supervisor Agent | COMPLIED | `TestForgeOrchestrator` preserved as coordinator |
| Do NOT implement Mutation Critic Agent | COMPLIED | Reserved for Phase 5 |
| Zero git commit / push operations | COMPLIED | No git mutations performed |

