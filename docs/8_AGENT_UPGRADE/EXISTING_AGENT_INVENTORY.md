# Existing Agent Inventory: Empirical Codebase Audit

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT COMPLETED  

---

## 1. Taxonomic Classification Standard

To avoid conflating procedural functions, execution tools, or workflow nodes with genuine autonomous cognitive agents, each candidate entity is evaluated against the following criteria:
- **Autonomous Goal & State:** Maintains internal decision criteria, goal representations, and memory.
- **Perception & Action:** Ingests structured environment feedback and produces deliberate actions or directives.
- **Tool / LLM Deliberation:** Employs an LLM or structured heuristic deliberation loop rather than a deterministic single-path script.

### Classification Categories:
- **Category A:** Implemented and runtime-verified (exercised in live hardening workflows and automated tests).
- **Category B:** Implemented but not runtime-verified (code complete, but lacks live pipeline execution traces).
- **Category C:** Partially implemented (skeleton, partial methods, or incomplete integration).
- **Category D:** Registered/configured but not actually executed (present in broker/config but bypassed at runtime).
- **Category E:** Documentation-only or placeholder (named in docs/comments without concrete implementation).

---

## 2. Exhaustive Inventory of Candidate Entities

### 2.1 Supervisor / Ingestion Entities

#### 1. TargetManagerAgent
- **Class & File:** `TargetManagerAgent` in [`testforge/ingestion.py:353`](file:///Users/sourabh/TestForge/testforge/ingestion.py#L353)
- **Framework:** Custom Python with optional Google GenAI Client (`from google import genai`)
- **Actual Responsibility:** Parses arbitrary Python files, discovers AST function signatures and classes, evaluates blast radius risks, resolves clean module names, and supports autonomous target code synthesis from natural language prompts.
- **Input Received:** File path string (`file_path: str`) or natural language specification prompt (`prompt: str`).
- **Output Produced:** `IngestionAnalysis` object containing function list, classes, methods, dependencies, AST tree, and module path.
- **Uses LLM?** Optional. Uses Gemini 2.5/3.6 Flash when synthesizing code from prompts (`synthesize_target_from_prompt`); uses pure Python `ast` for file ingestion (`ingest_file`).
- **Invokes Tools?** No direct external MCP calls; uses Python AST and filesystem I/O.
- **Reads/Writes Blackboard?** Writes `TargetSpace` indirectly via orchestrator checkpointing during Step 1.
- **Uses Pydantic?** Yes (`IngestionAnalysis` wraps attributes in a structured object).
- **Inter-Agent Communication:** Logs `AGENT_HANDOFF` to `TestGeneratorAgent` in `orchestrator.py:813`.
- **Instantiated?** Yes (`cli.py:65`, `github_service.py:634`, and exercised during AST ingestion).
- **Invoked in Live Hardening?** **Partially.** In live runs (`orchestrator.py:780`), AST parsing is performed using helper functions (`extract_function_signatures`, `BlastRadiusAnalyzer`), but `TargetManagerAgent` itself is formally represented as the sender of the initial handoff.
- **Classification:** **Category A (Implemented and runtime-verified)** in CLI/GitHub flows; **Category C (Partially implemented)** as an independent autonomous supervisor.

---

### 2.2 Test Generation Entities

#### 2. TestGeneratorAgent (Native / Legacy)
- **Class & File:** `TestGeneratorAgent` in [`testforge/agents.py:543`](file:///Users/sourabh/TestForge/testforge/agents.py#L543)
- **Framework:** Custom Python wrapping `HybridLLMClient` with deterministic AST synthesis fallback.
- **Actual Responsibility:** Generates initial unit test suites targeting function signatures, synthesizes nominal assert statements, and refines assertions when given critic feedback and surviving mutant diffs.
- **Input Received:** Target source code, missing branches (`List[str]`), surviving mutant diffs (`List[str]`), critic feedback text, iteration number.
- **Output Produced:** Python test suite source code string (`str`).
- **Uses LLM?** Yes (`HybridLLMClient` via Gemini, Ollama, or OpenRouter), with an offline AST deterministic fallback.
- **Invokes Tools?** Contains `ADKToolRegistry`, but in standard execution relies on internal AST synthesis methods.
- **Reads/Writes Blackboard?** Orchestrator updates `SuiteSpace` with its outputs.
- **Uses Pydantic?** Uses `GeneratedTestPayload` when operating via A2A; otherwise returns raw code string.
- **Inter-Agent Communication:** Receives handoff from `TargetManagerAgent`; hands off to `SubprocessSandbox`.
- **Instantiated?** Yes (`orchestrator.py:216`).
- **Invoked in Live Hardening?** Yes (active when `engine_mode == "legacy"` or when ADK mode falls back).
- **Classification:** **Category A (Implemented and runtime-verified)**.

#### 3. GoogleADKTestGenerator (Official ADK)
- **Class & File:** `GoogleADKTestGenerator` in [`testforge/adk_generator.py:330`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L330)
- **Framework:** Official **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`ADKModelBridge`)
- **Actual Responsibility:** Executes official Google ADK Runner pipeline to generate unit tests constrained by `GeneratedTestPayload`, validates AST syntax via `CodeSanitizer`, and checks intended mutant coverage against known IDs.
- **Input Received:** `target_source_code`, `existing_test_code`, `surviving_diffs`, `surviving_mutants`, `critic_directive`, `iteration`.
- **Output Produced:** Validated `GeneratedTestPayload` (test_code, coverage_intent, covered_mutants, imports).
- **Uses LLM?** Yes (`ADKModelBridge` connecting ADK runner to Gemini/Ollama/deterministic synthesis).
- **Invokes Tools?** Uses internal AST sanitization tools (`CodeSanitizer`).
- **Reads/Writes Blackboard?** Synchronizes validated test code to Blackboard `SuiteSpace`.
- **Uses Pydantic?** Yes (`GeneratedTestPayload` enforces strict validation).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:generator`. Exposes `handle_a2a_message()`. Exchanges messages with `CrewAICriticAgent`.
- **Instantiated?** Yes (`orchestrator.py:228`).
- **Invoked in Live Hardening?** Yes (active in `adk_crewai` mode and verified in live reflection run `wf_f20e4a6f8d9c`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.3 Critic / Mutation Analysis Entities

#### 4. AdversarialCriticAgent (Native)
- **Class & File:** `AdversarialCriticAgent` in [`testforge/agents.py:1165`](file:///Users/sourabh/TestForge/testforge/agents.py#L1165)
- **Framework:** Custom Python with `HybridLLMClient` and `ADKToolRegistry`.
- **Actual Responsibility:** Analyzes surviving mutant AST diffs, executes ADK tool deliberation (`tool_ast_audit`, `tool_compute_blast_radius`), and formulates targeted adversarial directives.
- **Input Received:** `target_code: str`, `surviving_mutant_diffs: List[str]`, `iteration: int`, `surviving_mutants`.
- **Output Produced:** Formatted critique directive string (`str`).
- **Uses LLM?** Yes (`HybridLLMClient` fallback or heuristic semantic analysis).
- **Invokes Tools?** Invokes `tool_ast_audit` and `tool_compute_blast_radius` via `ADKToolRegistry`.
- **Reads/Writes Blackboard?** Writes `CriticSpace.critic_directives`.
- **Uses Pydantic?** Internal tool contracts use Pydantic (`ToolDefinition`, `ToolCallResult`).
- **Inter-Agent Communication:** Receives surviving diffs from `SubprocessSandbox`; emits handoff to Generator.
- **Instantiated?** Yes (`orchestrator.py:222`).
- **Invoked in Live Hardening?** Yes (active in `legacy` engine mode and during fallback reflection loops).
- **Classification:** **Category A (Implemented and runtime-verified)**.

#### 5. MutationQualityCriticAgent / CrewAICriticAgent (Official CrewAI)
- **Class & File:** `MutationQualityCriticAgent` (aliased as `CrewAICriticAgent`) in [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py)
- **Framework:** Official **CrewAI**:
  - `crewai.Agent`
  - `crewai.Task`
  - `crewai.Crew`
  - `crewai.llms.base_llm.BaseLLM` (`CrewAILLMBridge`)
- **Actual Responsibility:** Upgraded in Phase 5 to perform dual responsibilities:
  1. **Mutation Analysis:** Consumes actual `MutantRecord` execution results from `TestExecutionAgent`, strictly classifying killed/survived/timed-out/invalid/equivalent mutants without fabrication.
  2. **Test Quality Analysis (`TestQualityAnalyzer`):** Deterministic AST inspection identifying weak assertions (`assert ... is not None`, `assert bool(...)`), tautological assertions (`assert True`, `assert not False`, `assert x == x`), missing assertions, broad exceptions (`pytest.raises(Exception)`), and missing boundary threshold values.
  3. **Adversarial Boundary Directives:** Formulates actionable, boundary-focused test directives and reflection iteration decisions (`should_iterate`).
- **Input Received:** `target_source_code: str`, `current_test_code: str`, `mutants: List[Any]`, `execution_payload`, `surviving_diffs: List[str]`, `iteration: int`.
- **Output Produced:** Validated `MutationQualityCriticPayload` and backward-compatible `CriticDirectivePayload`.
- **Uses LLM?** Yes (`CrewAILLMBridge` connected to TestForge multi-provider backend or deterministic fallback).
- **Invokes Tools?** Deterministic AST `TestQualityAnalyzer`.
- **Reads/Writes Blackboard?** Synchronizes findings and metrics to Blackboard `CriticSpace`.
- **Uses Pydantic?** Yes (`output_pydantic=CriticDirectivePayload`, payload contract `MutationQualityCriticPayload`).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:crewai:mutation-critic` and `agent:crewai:critic`. Handles `evaluate_quality`, `diagnose_mutants`, and `critique`.
- **Instantiated?** Yes (`orchestrator.py:231`).
- **Invoked in Live Hardening?** Yes (in Step F of reflection loop).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.4 Master Orchestrator

#### 6. TestForgeOrchestrator
- **Class & File:** `TestForgeOrchestrator` in [`testforge/orchestrator.py:137`](file:///Users/sourabh/TestForge/testforge/orchestrator.py#L137)
- **Framework:** Central imperative Python coordinator managing `TaskLifecycleFSM`, `Blackboard`, and `A2ABroker`.
- **Actual Responsibility:** Manages state transitions, enforces timeouts, coordinates MCP file ingestion, invokes baseline validation, controls mutation generation, executes reflection loops, and saves SQLite checkpoints.
- **Classification:** **Category A (Master Orchestrator / FSM)**.

---

### 2.4 Phase 3 Realized Specialist Agents (Google ADK)

#### 6. CodeIntelligenceAgent
- **Class & File:** `CodeIntelligenceAgent` in [`testforge/code_intelligence_agent.py:227`](file:///Users/sourabh/TestForge/testforge/code_intelligence_agent.py#L227)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`CodeIntelligenceModelBridge`)
- **Actual Responsibility:** Deep AST parsing, lexical scope resolution, cyclomatic complexity profiling, branch/condition discovery, boundary value extraction, and call graph construction.
- **Input Received:** `source_code: str`, `target_file_path: Optional[str]`, `job_id: str`.
- **Output Produced:** Strongly-typed `CodeIntelligencePayload` (functions, classes, branches, exceptions, dependencies, complexity, boundary targets).
- **Uses LLM?** Optional semantic reasoning via `CodeIntelligenceModelBridge`; authoritative deterministic AST analysis.
- **Invokes Tools?** Uses Python `ast`, `extract_function_signatures`, and `BlastRadiusAnalyzer`.
- **Reads/Writes Blackboard?** Writes `TargetSpace` and seeds `PlanSpace` with discovered boundary targets.
- **Uses Pydantic?** Yes (`CodeIntelligencePayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:code-intelligence`. Participates in `AGENT_HANDOFF` telemetry from `SecurityAgent`.
- **Instantiated?** Yes (`orchestrator.py:234`).
- **Invoked in Live Hardening?** Yes (exercised in live Step 1 ingestion and verified in `tests/test_phase3_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

#### 7. SecurityAgent
- **Class & File:** `SecurityAgent` in [`testforge/security_agent.py:228`](file:///Users/sourabh/TestForge/testforge/security_agent.py#L228)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`SecurityModelBridge`)
- **Actual Responsibility:** Continuous security oversight, prompt injection detection, AST policy enforcement (blocking `eval`, `exec`, `os.system`), credential redaction, and remediation recommendations.
- **Input Received:** `source_code: str`, `stage: str`, `job_id: str`.
- **Output Produced:** Strongly-typed `SecurityEvaluationPayload` (verdict, risk level, findings, defused text, redacted credentials, remediation notes).
- **Uses LLM?** Optional policy deliberation via `SecurityModelBridge`; deterministic guardrails remain authoritative.
- **Invokes Tools?** Uses `SecurityGuardrail`, `prompt_guard`, and `redact_sensitive_data`.
- **Reads/Writes Blackboard?** Writes `SecuritySpace` directly.
- **Uses Pydantic?** Yes (`SecurityEvaluationPayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:security`. Hands off to `CodeIntelligenceAgent`.
- **Instantiated?** Yes (`orchestrator.py:240`).
- **Invoked in Live Hardening?** Yes (exercised in live Step 0 security gate and verified in `tests/test_phase3_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.5 Phase 4 Realized Specialist Agents (Google ADK)

#### 8. TestPlanningAgent
- **Class & File:** `TestPlanningAgent` in [`testforge/planning_agent.py:186`](file:///Users/sourabh/TestForge/testforge/planning_agent.py#L186)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`PlanningModelBridge`)
- **Actual Responsibility:** Formulates structured nominal, boundary, negative, and exception scenarios from Code Intelligence findings. Computes McCabe cyclomatic complexity-based numeric priorities, performs SHA-256 fingerprint deduplication, and identifies mock dependencies.
- **Input Received:** `CodeIntelligencePayload` (or AST symbols), `job_id: str`, `allocated_test_budget: int`.
- **Output Produced:** Strongly-typed `TestPlanPayload` (scenarios, boundary_targets, negative_cases, mock_dependencies, status).
- **Uses LLM?** Optional semantic deliberation via `PlanningModelBridge`; deterministic scenario synthesis based on AST decisions.
- **Invokes Tools?** Uses Python `ast`, regex boundary value extraction, and `CodeIntelligenceAgent`.
- **Reads/Writes Blackboard?** Writes `PlanSpace` directly.
- **Uses Pydantic?** Yes (`TestPlanPayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:test-planner`. Receives handoff from `CodeIntelligenceAgent`; hands off to `TestGeneratorAgent`.
- **Instantiated?** Yes (`orchestrator.py:246`).
- **Invoked in Live Hardening?** Yes (exercised prior to candidate generation; verified in `tests/test_phase4_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

#### 9. TestExecutionAgent
- **Class & File:** `TestExecutionAgent` in [`testforge/execution_agent.py:227`](file:///Users/sourabh/TestForge/testforge/execution_agent.py#L227)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`ExecutionModelBridge`)
- **Actual Responsibility:** Coordinates subprocess test execution in isolated temporary environments via `ParallelSandboxRunner`. Enforces timeouts, collects pass/fail/error counts, extracts structured failure diagnostics with tracebacks, accurately measures line coverage via `pytest-cov`, and coordinates parallel mutant evaluation.
- **Input Received:** `test_code: str`, `target_code: str`, `measure_coverage: bool`, `timeout_seconds: Optional[float]`.
- **Output Produced:** Strongly-typed `TestExecutionPayload` (status, pass/fail/error counts, coverage %, duration, failures, stdout, stderr).
- **Uses LLM?** Optional execution diagnostics via `ExecutionModelBridge`.
- **Invokes Tools?** Coordinates `ParallelSandboxRunner` for subprocess isolation and `pytest-cov`.
- **Reads/Writes Blackboard?** Updates `ExecutionSpace` (`update_run`, `record_failure`) and `SuiteSpace` (`record_suite_execution`).
- **Uses Pydantic?** Yes (`TestExecutionPayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:test-execution`. Handles `execute_tests` and `evaluate_mutants` A2A requests.
- **Instantiated?** Yes (`orchestrator.py:252`).
- **Invoked in Live Hardening?** Yes (exercised during baseline validation, coverage measurement, and mutation evaluation; verified in `tests/test_phase4_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.6 Phase 5 Realized Specialist Critic (CrewAI)

#### 10. MutationQualityCriticAgent
- **Class & File:** `MutationQualityCriticAgent` (alias `CrewAICriticAgent`) in [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py)
- **Framework:** **CrewAI (v0.102.0)**:
  - `crewai.Agent`
  - `crewai.Task`
  - `crewai.Crew`
  - `crewai.llms.base_llm.BaseLLM` (`CrewAILLMBridge`)
- **Actual Responsibility:** Execution-evidence driven mutation analysis and deterministic AST test quality inspection (`TestQualityAnalyzer`). Strictly classifies mutants based solely on sandbox results (killed, survived, timed_out), flags weak/tautological assertions and missing boundaries, and computes exact mutation score without fabrication.
- **Input Received:** `target_source_code: str`, `current_test_code: str`, `mutants: List[MutantRecord]`, `execution_payload`.
- **Output Produced:** Strongly-typed `MutationQualityCriticPayload` and `CriticDirectivePayload`.
- **Uses LLM?** Yes (`CrewAILLMBridge` via CrewAI tasks) with deterministic offline fallback.
- **Invokes Tools?** Deterministic AST `TestQualityAnalyzer`.
- **Reads/Writes Blackboard?** Updates `CriticSpace` (`record_critic_evaluation`).
- **Uses Pydantic?** Yes (`MutationQualityCriticPayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:crewai:mutation-critic`. Handles `evaluate_quality`, `diagnose_mutants`, and `critique`.
- **Instantiated?** Yes (`orchestrator.py:258`).
- **Invoked in Live Hardening?** Yes (exercised in live reflection loop; verified in `tests/test_phase5_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.7 Phase 6 Realized Specialist Agent (Google ADK)

#### 11. ReflectionRepairAgent
- **Class & File:** `ReflectionRepairAgent` in [`testforge/reflection_agent.py`](file:///Users/sourabh/TestForge/testforge/reflection_agent.py)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`ReflectionModelBridge`)
- **Actual Responsibility:** Dedicated reflection and repair agent. Analyzes test execution failures and Mutation & Quality Critic findings, formulates targeted repair directives, coordinates surgical assertion repair with the generator, validates candidates against clean targets, and enforces strict non-regression (`candidate_score >= best_score`) with transparent stopping conditions.
- **Input Received:** `target_code: str`, `current_test_code: str`, `surviving_mutants: List[MutantRecord]`, `execution_failures`, `critic_payload`.
- **Output Produced:** Strongly-typed `RepairDirectivePayload`, `RepairResultPayload`, and `ReflectionDecisionPayload`.
- **Uses LLM?** Yes (`ReflectionModelBridge` via ADK `Runner.run_async()`) with deterministic offline deliberation fallback.
- **Invokes Tools?** Coordinates with test generator, sandbox test validator, and mutation evaluator.
- **Reads/Writes Blackboard?** Updates `SuiteSpace` (`record_repair_result`, `best_verified_test_code`, `repair_history`).
- **Uses Pydantic?** Yes (`RepairDirectivePayload`, `RepairResultPayload`, `ReflectionDecisionPayload` strictly enforced).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:reflection-repair`. Handles `plan_repair`, `repair_tests`, and `reflect`.
- **Instantiated?** Yes (`orchestrator.py:265`).
- **Invoked in Live Hardening?** Yes (exercised in live Step 4 reflection loop; verified in `tests/test_phase6_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.8 Phase 7 Realized Top-Level Supervisor Agent (Google ADK)

#### 12. SupervisorAgent
- **Class & File:** `SupervisorAgent` in [`testforge/supervisor_agent.py`](file:///Users/sourabh/TestForge/testforge/supervisor_agent.py)
- **Framework:** **Google Agent Development Kit (ADK v1.14.1)**:
  - `google.adk.agents.llm_agent.LlmAgent`
  - `google.adk.runners.Runner`
  - `google.adk.sessions.in_memory_session_service.InMemorySessionService`
  - `google.adk.models.base_llm.BaseLlm` (`SupervisorModelBridge`)
- **Actual Responsibility:** Authoritative top-level multi-agent supervisor. Coordinates workflow stage transitions across 10 canonical phases, validates workflow DAG legality, strictly enforces deterministic policy precedence over model deliberation (security gate, cancellations, timeouts, convergence thresholds, iteration & retry budgets), maintains truthful dynamic status for all 8 canonical agents, records structured decision traces on the Blackboard, and emits lifecycle events to telemetry.
- **Input Received:** Current `WorkflowStage` and contextual execution state (cancellation tokens, timeout deadlines, security results, test pass/fail results, mutation scores, iteration counters).
- **Output Produced:** Strongly-typed `SupervisorDecisionPayload` and `WorkflowTransitionRecord`.
- **Uses LLM?** Yes (`SupervisorModelBridge` via ADK `Runner.run_async()`) with deterministic fail-closed policy precedence.
- **Invokes Tools?** Coordinates with and delegates execution to specialist agents.
- **Reads/Writes Blackboard?** Updates `MetricsSpace` (`record_supervisor_decision`, `supervisor_decisions`, `current_stage`).
- **Uses Pydantic?** Yes (`SupervisorDecisionPayload`, `WorkflowTransitionRecord`, `WorkflowStage`, `SupervisorAction`).
- **Inter-Agent Communication:** Registered in `A2ABroker` as `agent:google-adk:supervisor`. Handles `decide_step` and `validate_transition`.
- **Instantiated?** Yes (`orchestrator.py:304`).
- **Invoked in Live Hardening?** Yes (exercised in live orchestrator pipeline across all stage transitions; verified in `tests/test_phase7_workflow_integration.py`).
- **Classification:** **Category A (Implemented and runtime-verified)**.

---

### 2.9 Non-Agent Subsystems (Often Conflated with Agents)

The following components are **tools, execution harnesses, or deterministic analyzers**, NOT independent cognitive agents:

| Subsystem Name | Concrete Class & File | Why It Is NOT an Agent | Correct Taxonomic Role |
| :--- | :--- | :--- | :--- |
| **SubprocessSandbox** | `ParallelSandboxRunner`<br>[`testforge/sandbox.py:196`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L196) | Spawns isolated pytest subprocesses across CPU cores. Has no autonomous goals, reasoning, or LLM capability. Coordinated by `TestExecutionAgent`. | **Execution Harness / Tool** |
| **ASTMutator** | `ASTMutator`<br>[`testforge/mutator.py:150`](file:///Users/sourabh/TestForge/testforge/mutator.py#L150) | Inverts comparison, arithmetic, and logical operators in Python AST syntax trees deterministically. | **Deterministic Code Mutator (Tool)** |
| **SecurityGuardrail** | `SecurityGuardrail`<br>[`testforge/security.py:239`](file:///Users/sourabh/TestForge/testforge/security.py#L239) | Executes regex patterns and AST visitors to detect prompt injections and dangerous primitives (`eval`, `exec`). Coordinated by `SecurityAgent`. | **Static Analysis & Inspection Guardrail** |
| **SemanticGuidanceEngine** | `SemanticGuidanceEngine`<br>[`testforge/guidance.py:110`](file:///Users/sourabh/TestForge/testforge/guidance.py#L110) | Formats surviving mutant diffs into structured strings with suggested verification boundaries. | **Semantic Guidance Utility** |
| **BlastRadiusAnalyzer** | `BlastRadiusAnalyzer`<br>[`testforge/blast_analyzer.py:45`](file:///Users/sourabh/TestForge/testforge/blast_analyzer.py#L45) | Traverses AST call graphs to count callers, callees, and estimate blast radius impact category (`LOW/MED/HIGH`). | **Static Call-Graph Analyzer (Tool)** |
| **MCPClientManager** | `MCPClientManager`<br>[`testforge/mcp_client.py:146`](file:///Users/sourabh/TestForge/testforge/mcp_client.py#L146) | Manages FastMCP client stdio connections and dispatches tool execution calls. | **MCP Protocol Client Transport** |

---

## 3. Summary of Existing Agent Counts

| Agent Name | Framework | Category | Live Runtime Verified? |
| :--- | :--- | :---: | :---: |
| `SupervisorAgent` *(PHASE 7)* | Google ADK (`LlmAgent`) | **A** | Yes (live top-level workflow supervisor) |
| `TargetManagerAgent` | Custom Python / GenAI | **A/C** | Yes (in CLI/Ingestion flows) |
| `CodeIntelligenceAgent` *(PHASE 3)* | Google ADK (`LlmAgent`) | **A** | Yes (live Step 1 AST intelligence) |
| `SecurityAgent` *(PHASE 3)* | Google ADK (`LlmAgent`) | **A** | Yes (live Step 0 gatekeeper) |
| `TestPlanningAgent` *(PHASE 4)* | Google ADK (`LlmAgent`) | **A** | Yes (live scenario formulation & prioritization) |
| `TestExecutionAgent` *(PHASE 4)* | Google ADK (`LlmAgent`) | **A** | Yes (live sandbox validation & coverage) |
| `TestGeneratorAgent` | Custom Python / HybridLLM | **A** | Yes (in legacy/fallback mode) |
| `GoogleADKTestGenerator` | Google ADK (`LlmAgent`) | **A** | Yes (in `adk_crewai` mode) |
| `MutationQualityCriticAgent` *(PHASE 5)* | CrewAI (`Agent`/`Crew`) | **A** | Yes (in live critic workflow) |
| `ReflectionRepairAgent` *(PHASE 6)* | Google ADK (`LlmAgent`) | **A** | Yes (in live reflection loop) |
| `AdversarialCriticAgent` | Custom Python / Heuristic | **A** | Yes (in legacy/fallback mode) |
| `TestForgeOrchestrator` | Central Procedural Execution Engine | **A** | Yes (execution engine & compatibility layer) |

- **Canonical 8-Agent Modular Architecture Topology:**
  1. `SupervisorAgent` (Google ADK)
  2. `CodeIntelligenceAgent` (Google ADK)
  3. `TestPlanningAgent` (Google ADK)
  4. `TestGeneratorAgent` / `GoogleADKTestGenerator` (Google ADK)
  5. `TestExecutionAgent` (Google ADK)
  6. `CrewAICriticAgent` / `MutationQualityCriticAgent` (CrewAI)
  7. `SecurityAgent` (Google ADK)
  8. `ReflectionRepairAgent` (Google ADK)
- **Active in Live Pipeline Run:** All **8** canonical specialist agents actively participate and are dynamically tracked via the Wiretap API.

