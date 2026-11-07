# Current Architecture Audit: TestForge Hardening Pipeline

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT COMPLETED  

---

## 1. Executive Architectural Overview

TestForge currently operates as a **hybrid multi-agent system driven by a centralized imperative orchestrator** (`TestForgeOrchestrator` in [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py)). 

While the system integrates two major agentic frameworks—**Google Agent Development Kit (ADK v1.14.1)** and **CrewAI (v1.15.28)**—as well as an in-process **Agent-to-Agent (A2A) broker** ([`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py)), top-level lifecycle coordination is presently driven procedurally by an imperative finite state machine (`TaskLifecycleFSM`) within `TestForgeOrchestrator`.

```
                                +-----------------------------+
                                |  FastAPI Web Cockpit        |
                                |  (server.py / REST & WS)    |
                                +--------------+--------------+
                                               |
                                               v
                        +---------------------------------------------+
                        |        TestForgeOrchestrator (Central)      |
                        |   - TaskLifecycleFSM State Transitions      |
                        |   - Checkpointing & Timeout Enforcement     |
                        |   - Sequential Step Orchestration           |
                        +-------+-------------+-------------+---------+
                                |             |             |
           +--------------------+             |             +--------------------+
           v                                  v                                  v
+-----------------------+          +--------------------+          +---------------------------+
| Ingestion & Security  |          | In-Process A2A     |          | Execution & Mutation      |
| - TargetManagerAgent  |          | Message Broker     |          | - ParallelSandboxRunner   |
|   (testforge/ingest)  |          | (testforge/a2a.py) |          |   (testforge/sandbox.py)  |
| - SecurityGuardrail   |          +----+----------+----+          | - ASTMutator              |
|   (testforge/sec.py)  |               |          |               |   (testforge/mutator.py)  |
+-----------------------+               v          v               +---------------------------+
                                   +---------+   +---------+
                                   | Google  |   | CrewAI  |
                                   | ADK Gen |   | Critic  |
                                   +---------+   +---------+
                                        ^             ^
                                        |             |
                                  +-----+-------------+-----+
                                  |    Shared Blackboard    |
                                  | (testforge/blackboard)  |
                                  | - TargetSpace           |
                                  | - MutantSpace           |
                                  | - CriticSpace           |
                                  | - SuiteSpace            |
                                  | - MetricsSpace          |
                                  | - SQLite Checkpointing  |
                                  +-------------------------+
```

---

## 2. Framework Integration Audit

### 2.1 Google ADK (Agent Development Kit v1.14.1)

#### Initialization & Instantiation
Google ADK is initialized in [`testforge/adk_generator.py:330`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L330) inside `GoogleADKTestGenerator.__init__`:
- **Instantiated ADK Class:** `google.adk.agents.llm_agent.LlmAgent`
- **Runner Class:** `google.adk.runners.Runner`
- **Session Service:** `google.adk.sessions.in_memory_session_service.InMemorySessionService`
- **Model Bridge:** `ADKModelBridge`, a subclass of `google.adk.models.base_llm.BaseLlm` that connects the ADK runner to TestForge's `HybridLLMClient` or deterministic AST synthesis.
- **Contract Enforcement:** `output_schema=GeneratedTestPayload`.

#### Workflow Constructs
- **SequentialAgent / ParallelAgent / LoopAgent:** **NOT used in the current codebase.**
- Although `google.adk.agents.sequential_agent.SequentialAgent`, `ParallelAgent`, and `LoopAgent` are installed in the virtual environment, the existing architecture only instantiates an isolated `LlmAgent`.
- Looping and iteration are managed externally by Python `while` and `for` loops inside `TestForgeOrchestrator._execute_pipeline`.

#### ADK Engine Tool Deliberation Layer
- In [`testforge/adk_engine.py`](file:///Users/sourabh/TestForge/testforge/adk_engine.py), TestForge maintains a custom `ADKToolRegistry` simulating tool deliberation:
  - `tool_execute_sandbox`
  - `tool_compute_blast_radius`
  - `tool_inspect_git_diff`
  - `tool_ast_audit`
- Invocations are recorded as `ADK_TOOL_CALL` telemetry events in `testforge_trace.jsonl`.
- **Finding:** `ADKToolRegistry` in `testforge/adk_engine.py` is a custom internal tool harness, not the official `google.adk.tools.BaseTool` or `McpToolset`.

### 2.2 CrewAI (v1.15.28)

#### Initialization & Instantiation
CrewAI is initialized in [`testforge/crew_critic.py:194`](file:///Users/sourabh/TestForge/testforge/crew_critic.py#L194) inside `CrewAICriticAgent.__init__`:
- **Instantiated CrewAI Classes:** `crewai.Agent`, `crewai.Task`, and `crewai.Crew`.
- **LLM Bridge:** `CrewAILLMBridge`, a subclass of `crewai.llms.base_llm.BaseLLM` connecting CrewAI task execution to TestForge's `HybridLLMClient`.
- **Contract Enforcement:** `output_pydantic=CriticDirectivePayload`.
- **Configuration:** Telemetry is opted out (`CREWAI_TELEMETRY_OPT_OUT=true`, `OTEL_SDK_DISABLED=true`), and delegation is disabled (`allow_delegation=False`).

#### Execution Path
- When `engine_mode == "adk_crewai"` (or during A2A message dispatch), the orchestrator invokes `self.crew_critic.diagnose_mutants(...)`.
- A genuine `Crew` is constructed on each reflection cycle with one `Agent` and one `Task`, returning structured `CriticDirectivePayload`.

### 2.3 Framework Coexistence & Competition Analysis

- **Do ADK and CrewAI compete for top-level orchestration?**
  **No.** In the current codebase, neither framework acts as the master orchestrator. Instead, both are invoked as **subordinate specialists** by `TestForgeOrchestrator`:
  - Google ADK (`GoogleADKTestGenerator`) is invoked strictly to synthesize test code (`generate_tests`).
  - CrewAI (`CrewAICriticAgent`) is invoked strictly to diagnose surviving mutants (`diagnose_mutants`).
- **Framework Duality & Duplication:**
  The codebase maintains a dual implementation for both roles:
  1. **Generator Duality:** Native `TestGeneratorAgent` ([`testforge/agents.py:543`](file:///Users/sourabh/TestForge/testforge/agents.py#L543)) vs. `GoogleADKTestGenerator` ([`testforge/adk_generator.py:330`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L330)).
  2. **Critic Duality:** Native `AdversarialCriticAgent` ([`testforge/agents.py:1165`](file:///Users/sourabh/TestForge/testforge/agents.py#L1165)) vs. `CrewAICriticAgent` ([`testforge/crew_critic.py:194`](file:///Users/sourabh/TestForge/testforge/crew_critic.py#L194)).
  Depending on `engine_mode` (`"adk_crewai"` vs `"legacy"`), the orchestrator branches between them.

---

## 3. End-to-End Workflow Execution Trace

Tracing a complete live run from REST API submission (`samples/discount.py`) to completion:

| Step # | Nominal Workflow Stage | Executing Component | Concrete File & Line | Input Data | Output Produced | Blackboard State Changes |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | **Input Security Screening** | `SecurityGuardrail` | [`testforge/security.py:239`](file:///Users/sourabh/TestForge/testforge/security.py#L239)<br>Called at `orchestrator.py:654` | Raw Python source code string | `InputSecurityResult` (allowed: bool, risk_level, findings) | None (Fails closed if injection or policy violation detected) |
| **1** | **Ingestion & Symbol Analysis** | `TestForgeOrchestrator` via `BlastRadiusAnalyzer` & `MCPClientManager` | [`testforge/orchestrator.py:718-825`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L718)<br>Uses [`testforge/blast_analyzer.py`](file:///Users/sourabh/TestForge/testforge/blast_analyzer.py) | Target source code & file path | Function signatures, call graph, blast radius risk (`LOW/MED/HIGH`) | `TargetSpace` populated; checkpoint saved (`INITIAL_INGESTION`) |
| **2** | **Initial Test Generation** | `TestGeneratorAgent` or `GoogleADKTestGenerator` | [`testforge/orchestrator.py:843-920`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L843) | Target source code & AST metadata | Candidate pytest test suite code | `SuiteSpace.candidate_test_code` updated |
| **3** | **Clean Baseline Validation (pass@1)** | `ParallelSandboxRunner` (`SubprocessSandbox`) | [`testforge/sandbox.py:196`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L196)<br>Called at `orchestrator.py:938` | Candidate test code & clean target code | `CandidateSuiteValidationResult` (passed, failed, syntax error) | `SuiteSpace.current_test_code` set; `MetricsSpace.baseline_passed` |
| **4** | **Baseline Line Coverage Measurement** | `ParallelSandboxRunner.measure_coverage` | [`testforge/sandbox.py:365`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L365)<br>Called at `orchestrator.py:1085` | Clean test code + `pytest --cov --cov-report=json` | `(coverage_pct, coverage_data_dict)` | `MetricsSpace.line_coverage` updated |
| **5** | **Deterministic Mutation Injection** | `ASTMutator.mutate` | [`testforge/mutator.py:150`](file:///Users/sourabh/TestForge/testforge/mutator.py#L150)<br>Called at `orchestrator.py:1218` | Target source code & target lines | `List[MutantRecord]` with AST diffs & mutated code | `MutantSpace.mutants` populated |
| **6** | **Parallel Mutant Evaluation** | `ParallelSandboxRunner.evaluate_mutants_parallel` | [`testforge/sandbox.py:232`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L232)<br>Called at `orchestrator.py:1238` | Mutants list + test code + timeout (5s) | Evaluated mutants (KILLED, SURVIVED, TIMEOUT) | `MutantSpace.mutants` updated; `MetricsSpace.mutation_score` |
| **7** | **Equivalence Analysis** | `EquivalentMutantAnalyzer.classify_mutants` | [`testforge/equivalence.py:120`](file:///Users/sourabh/TestForge/testforge/equivalence.py#L120)<br>Called at `orchestrator.py:1275` | Surviving mutants + AST diffs | Equivalent vs killable classifications | `MutantSpace.equivalent_mutants` set; adjusted score computed |
| **8** | **Critic Diagnosis & Directive Formulation** | `CrewAICriticAgent` or `AdversarialCriticAgent` | [`testforge/crew_critic.py:230`](file:///Users/sourabh/TestForge/testforge/crew_critic.py#L230)<br>Called at `orchestrator.py:1485` | Surviving mutant diffs & target source code | `CriticDirectivePayload` (directives, failure mechanisms) | `CriticSpace.critic_directives` appended |
| **9** | **Hardened Test Synthesis (Reflection)** | `GoogleADKTestGenerator` or `TestGeneratorAgent` | [`testforge/adk_generator.py:380`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L380)<br>Called at `orchestrator.py:1140` | Existing tests + Critic directives + surviving diffs | Hardened test suite with targeted assertions | `SuiteSpace.hardened_test_code` updated |
| **10** | **Final State Persistence & Reporting** | `TestForgeOrchestrator` & `SQLiteBlackboardStorage` | [`testforge/orchestrator.py:1550-1600`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L1550)<br>Uses [`testforge/persistence.py`](file:///Users/sourabh/TestForge/testforge/persistence.py) | Final `TestForgeState` snapshot | Checkpoint in SQLite DB + JSON response to frontend | Final snapshot saved; WebSocket push dispatched |

---

## 4. Architectural Deficiencies & Missing Cognitive Boundaries

The current architecture, while robust and passing 642 regression tests, has key limitations that the 8-Agent upgrade will address:

1. **Centralized Procedural Orchestration:**
   `TestForgeOrchestrator` is a 1,650-line procedural class. It handles CLI parsing, MCP tool dispatch, FSM transitions, subprocess spawning, SQLite serialization, and fallback branching in a single imperative file.
2. **Missing Test Planning Entity:**
   There is no separate **Test Planning Agent**. Tests are either generated in one shot from function signatures or updated against surviving mutant diffs. Scenario selection, equivalence partitioning, boundary condition mapping, and test budgeting are conflated inside the generation prompt or AST synthesizer.
3. **Execution is Handled as a Subprocess Tool, Not an Agent:**
   Execution is performed directly by `ParallelSandboxRunner` without an autonomous **Test Execution Agent** capable of test triage, flakiness detection, assertion isolation, or dynamic timeout adjustment.
4. **Security is an Input/Output Filter, Not an Active Agent:**
   `SecurityGuardrail` is a synchronous validation utility called at Step 0. There is no autonomous **Security Agent** monitoring tool interactions, evaluating generated test safety dynamically, or enforcing least-privilege sandboxing throughout the reflection loop.
5. **Code Intelligence is Conflated with Ingestion:**
   Static AST parsing, call graph building, and blast radius analysis are executed as procedural utilities within `TargetManagerAgent` and `BlastRadiusAnalyzer`, rather than being exposed by a dedicated **Code Intelligence Agent**.
6. **Reflection & Repair is Merged with Initial Generation:**
   `TestGeneratorAgent` and `GoogleADKTestGenerator` perform both initial baseline synthesis (pass@1) and iterative reflection repair. These are fundamentally different cognitive tasks: synthesis requires comprehensive API coverage, while repair requires surgical differential assertion hardening.

