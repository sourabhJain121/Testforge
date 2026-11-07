# TestForge Phase 7 Pre-Implementation Architecture Audit

**Repository:** `/Users/sourabh/TestForge`  
**Date:** November 5, 2026  
**Auditor:** Principal AI Systems Architect & Lead Evaluation Reviewer  
**Scope:** Top-Level Supervisor Agent & Eight-Agent Workflow Orchestration  

---

## 1. What currently controls the complete hardening workflow?

Currently, the complete hardening workflow is controlled by the imperative, procedural method `TestForgeOrchestrator._execute_pipeline()` in [`testforge/orchestrator.py:770-1750`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L770).

`TestForgeOrchestrator` maintains:
1. An internal finite state machine `TaskLifecycleFSM` (`state.py:27`) tracking lifecycle states (`CREATED`, `INGESTING`, `PLANNING`, `GENERATING_TESTS`, `EXECUTING`, `MUTATION_ANALYSIS`, `EVALUATING`, `COMPLETED`, `FAILED`, `CANCELLED`).
2. An imperatively coded sequence of stages:
   - Step 0: Security screening (`SecurityAgent`).
   - Step 1: AST ingestion & symbol extraction (`CodeIntelligenceAgent`).
   - Step 1.5: Scenario planning (`TestPlanningAgent`).
   - Step 2: Initial candidate test generation (`GoogleADKTestGenerator`).
   - Step 3: Sandbox validation (pass@1 check) and line coverage (`TestExecutionAgent`).
   - Step 4: Iterative reflection & hardening loop (1 to `max_iterations`):
     - Targeted reflection & test repair (`ReflectionRepairAgent`).
     - Granular candidate validation (`ParallelSandboxRunner`).
     - Mutation injection (`ASTMutator`).
     - Mutant evaluation (`TestExecutionAgent`).
     - Mutation score calculation & equivalence analysis (`calculate_mutation_scores`).
     - Adversarial & quality evaluation (`MutationQualityCriticAgent`).
     - Termination condition evaluation.
3. Checkpoint persistence and restoration via SQLite (`Blackboard.save_checkpoint`).

---

## 2. Which orchestration decisions are currently made inside `TestForgeOrchestrator`?

The following orchestration decisions are made imperatively within `TestForgeOrchestrator`:
1. **MCP Tool Need Decision:** Whether to invoke MCP tools (`read_text_file`, `get_file_info`, `get_repository_info`) based on missing target content (`orchestrator.py:802-850`).
2. **Security Gate Clearance / Refusal:** Terminating pipeline if `SecurityAgent` or `SecurityGuardrail` marks input as blocked/refused (`orchestrator.py:813-834`).
3. **AST Ingestion vs Checkpoint Resume:** Deciding whether to skip ingestion if resuming from a checkpoint (`orchestrator.py:797-974`).
4. **Initial Suite Generation Need:** Deciding whether to generate initial tests or use existing/restored test code (`orchestrator.py:981`).
5. **Baseline Failure Self-Repair:** Deciding to trigger a single self-repair attempt if pass@1 clean validation fails (`orchestrator.py:1107-1130`).
6. **Coverage Sufficiency Decision:** Deciding whether to proceed to mutation analysis or fail early if baseline tests achieve zero coverage or fail execution (`orchestrator.py:1260-1290`).
7. **Equivalence & Mutant Filtering:** Deciding which mutants are presented to the Critic as surviving diffs (`orchestrator.py:1548-1555`).
8. **Loop Convergence & Stopping Conditions:**
   - Terminating if `effective_score >= target_mutation_score and cov_pct > 0.0` (`orchestrator.py:1644-1660`).
   - Terminating if `iteration == max_iterations` (`orchestrator.py:1662-1678`).
   - Terminating on timeout or user cancellation (`orchestrator.py:350, 980, 1080, 1330`).
   - Terminating if mutation generation or execution fails (`orchestrator.py:1440, 1507`).

---

## 3. Which agent handoffs are direct method calls versus A2A messages?

In the current codebase (Phases 1-6):
- **A2A Broker Handled:**
  - `agent:google-adk:generator`: Invoked via `broker.send_message(req)` during initial generation (`orchestrator.py:1001-1016`). Fallback to direct method call `self.generator.generate_tests(...)` if A2A or ADK fails.
  - `agent:google-adk:reflection-repair`: Invoked via `broker.send_message(req)` during Step 4 reflection loop (`orchestrator.py:1349-1366`).
  - `agent:crewai:mutation-critic` / `agent:crewai:critic`: Invoked via `broker.send_message(req)` in Step 4 critic evaluation (`orchestrator.py:1571-1588`). Fallback to direct call `self.crew_critic.evaluate_quality(...)`.
- **Direct Method Calls (with logged AGENT_HANDOFF events):**
  - `self.security_agent.evaluate_code(...)` / `inspect_input(...)`
  - `self.code_intel_agent.analyze_source(...)`
  - `self.planning_agent.plan_tests(...)`
  - `self.execution_agent.execute_tests(...)` and `self.execution_agent.evaluate_mutants(...)`
- All agents have `handle_a2a_message()` implemented and registered with `A2ABroker`, but `TestForgeOrchestrator` calls some directly while logging handoff events to `TraceLogger`.

---

## 4. Which decisions are deterministic, and which use LLM reasoning?

- **Deterministic Decisions (Hard Invariants):**
  - Security refusal: If AST security scanner detects forbidden primitives (`eval`, `exec`, `os.system`) or high prompt injection risk, refusal is mandatory and immediate.
  - Sandbox execution permission: Tests are executed only within isolated temporary directory subprocesses with strict timeout (5.0s) and thread-safe cancellation token checks.
  - Test validation outcome: Pass@1 is based strictly on pytest exit code and collected failure counts.
  - Mutant survival/killing: Based strictly on pytest failure/error on the mutated codebase. No mutant is ever declared killed without execution proof.
  - Mutation score formula: `round((len(killed) / denominator) * 100.0, 2)` where denominator = `killed + survived + timed_out`.
  - Termination condition: Checking `score >= target_score` and `iteration >= max_iterations`.
  - Non-regression check: Rejecting candidate suites whose score < previous verified score.
- **LLM Reasoning (Cognitive Heuristics):**
  - Test generation: Synthesizing Python pytest code matching signatures and scenarios (`GoogleADKTestGenerator`).
  - Planning: Formulating edge-case and boundary scenarios (`TestPlanningAgent`).
  - Critic qualitative analysis: Explaining why a mutant survived and suggesting semantic invariants (`MutationQualityCriticAgent`).
  - Reflection repair: Deciding how to rewrite test assertions to target surviving mutant mechanics (`ReflectionRepairAgent`).

---

## 5. How is Blackboard state provided to each agent?

- Each agent receives the `Blackboard` instance at construction time (`self.blackboard = blackboard`).
- During execution, agents read from relevant typed partitions:
  - `CodeIntelligenceAgent` reads/writes `TargetSpace`.
  - `SecurityAgent` reads `TargetSpace` and writes `SecuritySpace`.
  - `TestPlanningAgent` reads `TargetSpace` and writes `PlanSpace`.
  - `TestExecutionAgent` reads `SuiteSpace`, writes `ExecutionSpace`.
  - `MutationQualityCriticAgent` reads `MutantSpace`, `ExecutionSpace`, writes `CriticSpace`.
  - `ReflectionRepairAgent` reads `CriticSpace`, `ExecutionSpace`, writes `SuiteSpace`.
- Inter-agent messages dispatched through `A2ABroker` trigger automatic partition synchronization hooks (`_sync_code_intel_to_blackboard`, `_sync_security_to_blackboard`, `_sync_plan_to_blackboard`, `_sync_execution_to_blackboard`, `_sync_critique_to_blackboard`, `_sync_reflection_to_blackboard`).

---

## 6. How are job IDs, source hashes, test-suite hashes, and iteration IDs preserved?

- **Job ID & Task ID:** Generated at start (`wf_{hex}` or user-supplied `job_id`), propagated through `TestForgeState.task_id`, `TraceLogger.context`, every `A2AMessage.correlation_id`, and all Pydantic payloads (`task_id`, `job_id`).
- **Source Hash (`source_sha`):** Computed as SHA-256 of normalized target code string in `TargetSpace.source_sha`, propagated into `CodeIntelligencePayload`, `TestPlanPayload`, `MutationQualityCriticPayload`, and `RepairDirectivePayload`.
- **Test-Suite Hash (`test_sha`):** Computed as SHA-256 of candidate/hardened test code in `TestExecutionPayload.test_sha`, `MutationQualityCriticPayload.test_sha`, and `RepairResultPayload.candidate_test_sha`.
- **Iteration ID:** Explicit integer tracking in `TestForgeState.current_iteration`, `MetricsSpace.current_iteration`, and `IterationMetrics.iteration_index`.

---

## 7. How are cancellation, timeout, failure, and retry handled?

- **Cancellation:** Orchestrator holds `self.cancel_event = threading.Event()`. Called at every stage transition via `self.check_cancellation_or_timeout()`. Sandbox workers inspect the cancel event and terminate child processes immediately.
- **Timeout:** `self.timeout_seconds` (default 300s) compared against `time.time() - self.start_time`. Expiration sets `state.terminated = True`, state `TIMED_OUT`.
- **Failure:** Errors in tool calls or validation set lifecycle state `FAILED` with a structured `termination_reason`.
- **Retry:** Bounded retries (e.g. single self-repair on baseline test compilation error; bounded reflection loop iterations 1 to `max_iterations`). Retries are idempotent and bounded.

---

## 8. Which workflow steps must remain deterministic for security and reliability?

1. **Step 0 Security Gate:** Input code must pass deterministic AST static analysis and regex guardrails before being executed in any sandbox or passed to external APIs.
2. **Sandbox Permission & Isolation:** Subprocess isolation, temp directory cleanup, and 5s timeout enforcement must remain purely deterministic.
3. **Cancellation & Timeout Enforcement:** Immediate cessation of execution without model negotiation.
4. **Mutant Execution & Status Classification:** Status determination (`KILLED`, `SURVIVED`, `TIMED_OUT`) is calculated directly from pytest process return codes and stderr/stdout parsing.
5. **Score Calculation & Non-Regression Invariant:** Score is computed mathematically. Candidate test suites with lower mutation scores or breaking clean code must be deterministically rejected.
6. **Maximum Iteration Bound:** The loop must terminate deterministically when `iteration >= max_iterations`.

---

## 9. What is the smallest safe way to introduce a genuine Supervisor without replacing the existing system?

The optimal, non-destructive architectural pattern:
1. **Implement `SupervisorAgent` in `testforge/supervisor_agent.py`:**
   - Google ADK `LlmAgent` + `Runner` + `InMemorySessionService` + `SupervisorModelBridge(BaseLlm)`.
   - Explicit workflow state machine (`WorkflowStage`: `INITIALIZING`, `SECURITY_SCREENING`, `CODE_INTELLIGENCE`, `TEST_PLANNING`, `TEST_GENERATION`, `BASELINE_EXECUTION`, `MUTATION_EVALUATION`, `CRITIC_ASSESSMENT`, `REFLECTION_REPAIR`, `HARDENING_CONVERGED`, `FAILED`, `CANCELLED`).
   - Strongly-typed Pydantic contract: `SupervisorDecisionPayload` declaring next action, target agent, inputs, reason, and `is_deterministic`.
   - **Deterministic Guard Enforcement:** The Supervisor evaluates deterministic policies first (security check, cancellation, timeouts, iteration bounds, score convergence). If a deterministic policy applies, it issues an authoritative deterministic decision. When in an exploratory or planning step, it leverages Google ADK deliberation.
2. **Integrate into `TestForgeOrchestrator`:**
   - Instantiate `self.supervisor = SupervisorAgent(...)` and register with `self.broker` as `agent:google-adk:supervisor`.
   - In `_execute_pipeline()`, before executing each stage transition, consult `self.supervisor.decide_next_step(...)`.
   - The orchestrator validates the supervisor decision against allowed state transitions (`SupervisorAgent.validate_transition`), records the decision in Blackboard and Wiretap telemetry, and executes the approved step.
   - If the supervisor decides `STOP_CONVERGED`, `STOP_MAX_ITERATIONS`, `STOP_SECURITY_REFUSAL`, or `STOP_CANCELLED`, orchestrator cleanly wraps up and persists results.
3. **Preserve Compatibility:**
   - `TestForgeOrchestrator` remains the outward-facing execution engine for REST API (`server.py`), CLI (`cli.py`), and benchmarks.
   - All existing method signatures and tests remain untouched.

