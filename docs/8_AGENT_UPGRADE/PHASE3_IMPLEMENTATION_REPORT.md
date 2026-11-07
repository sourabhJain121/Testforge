# TestForge Phase 3 Implementation Report: Code Intelligence and Security Agent Realization

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Implementation Date:** November 4, 2026  
**Auditor / Implementer:** Principal AI Systems Architect & Lead Evaluation Reviewer  
**Phase Status:** COMPLETED & VERIFIED  

---

## Executive Summary

Phase 3 of the 8-Agent Modular Architecture Upgrade has been successfully implemented and verified. Two genuine Google ADK cognitive agents—**`CodeIntelligenceAgent`** and **`SecurityAgent`**—have been realized and integrated into the live TestForge hardening workflow.

Key achievements in Phase 3:
1. **Google ADK Code Intelligence Agent:** Built [`testforge/code_intelligence_agent.py`](file:///Users/sourabh/TestForge/testforge/code_intelligence_agent.py) with official `google.adk.agents.llm_agent.LlmAgent`, `Runner`, and `BaseLlm` bridge (`CodeIntelligenceModelBridge`). Performs deep deterministic AST symbol extraction, lexical scope resolution, cyclomatic complexity profiling, comparison operator threshold identification, exception path extraction, and call-graph analysis. Emits strongly-typed `CodeIntelligencePayload` and synchronizes to `TargetSpace` and `PlanSpace`.
2. **Google ADK Security Agent:** Built [`testforge/security_agent.py`](file:///Users/sourabh/TestForge/testforge/security_agent.py) with official `google.adk.agents.llm_agent.LlmAgent`, `Runner`, and `BaseLlm` bridge (`SecurityModelBridge`). Enforces multi-layer security oversight: deterministic prompt injection screening, AST policy enforcement (strictly blocking `eval`, `exec`, `os.system`), indirect prompt injection defusing in docstrings/comments, and credential/API key redaction. Emits strongly-typed `SecurityEvaluationPayload` and synchronizes to `SecuritySpace`.
3. **Live Workflow Integration:** Both agents are genuine participants in [`TestForgeOrchestrator`](file:///Users/sourabh/TestForge/testforge/orchestrator.py). `SecurityAgent` guards the entry point (Step 0) and fails closed on policy violations. `CodeIntelligenceAgent` analyzes target source code (Step 1), seeds boundary conditions to `PlanSpace`, records `AGENT_HANDOFF` telemetry, and persists findings in state metadata and SQLite checkpoints.
4. **Authoritative In-Process A2A Protocol:** Registered both agents in `A2ABroker` as `agent:google-adk:code-intelligence` and `agent:google-adk:security`, with automatic Blackboard synchronization on `INFORM` performatives.
5. **Zero-Regression Verification:** Verified through 21 focused tests (100% pass) and the full TestForge regression test suite (**675 passed, 0 failed, 348 warnings in 356.13s**).

---

## 1. Concrete Agent Implementations

### 1.1 CodeIntelligenceAgent (`testforge/code_intelligence_agent.py`)
- **Framework:** Google Agent Development Kit (ADK v1.14.1):
  - Agent: `LlmAgent(name="code_intelligence_agent", model=self.model_bridge, output_schema=CodeIntelligencePayload)`
  - Session Service: `InMemorySessionService`
  - Runner: `Runner(agent=self.adk_agent, session_service=self.session_service, app_name="testforge")`
  - Model Bridge: `CodeIntelligenceModelBridge(BaseLlm)` connecting runner deliberation to deterministic AST analysis and optional live LLM reasoning.
- **Analysis Capabilities:**
  - **Lexical Scope Extraction:** Identifies module-level functions, class definitions, instance/classmethod/staticmethod methods, argument signatures, and return annotations via `extract_function_signatures`.
  - **Branch & Condition Discovery:** Traverses `ast.If`, `ast.While`, `ast.For`, `ast.Match` using `_BranchAndExceptionVisitor`. Extracts unparsed condition strings, line numbers, relational operators, and comparison threshold constants.
  - **Exception Path Extraction:** Detects `ast.Raise` (exception types, error messages) and `ast.Try` (exception handlers, finally/else blocks).
  - **Cyclomatic Complexity Profiling:** Computes McCabe cyclomatic complexity per function (decision points + 1) and module averages.
  - **Impact & Call Graph:** Builds adjacency call graphs via `BlastRadiusAnalyzer.build_call_graph` and computes blast risk (`LOW`, `MEDIUM`, `HIGH`).
  - **Testing Target Prioritization:** Ranks functions by cyclomatic complexity and risk profiles.
- **Contract:** Outputs validated [`CodeIntelligencePayload`](file:///Users/sourabh/TestForge/testforge/a2a.py#L213).
- **Blackboard Updates:**
  - Writes functions, classes, dependencies, branches, exception paths, and complexity metrics to `TargetSpace`.
  - Seeds discovered comparison threshold constants into `PlanSpace.boundary_conditions`.

### 1.2 SecurityAgent (`testforge/security_agent.py`)
- **Framework:** Google Agent Development Kit (ADK v1.14.1):
  - Agent: `LlmAgent(name="security_agent", model=self.model_bridge, output_schema=SecurityEvaluationPayload)`
  - Session Service: `InMemorySessionService`
  - Runner: `Runner(agent=self.adk_agent, session_service=self.session_service, app_name="testforge")`
  - Model Bridge: `SecurityModelBridge(BaseLlm)` for policy remediation guidance.
- **Security Boundaries & Invariants Enforced:**
  - **Deterministic Authoritativeness:** Underlying `SecurityGuardrail` checks are authoritative; an LLM cannot approve or downgrade prohibited code.
  - **No Untrusted Execution:** Untrusted code is never executed during security analysis.
  - **Zero Secret Exposure:** Credentials and API keys (e.g., `sk-live-...`, `AKIA...`) are identified and redacted from prompts and traces via `redact_sensitive_data`.
  - **Multi-Layer Analysis:**
    1. Input Prompt Injection: Rejects direct instruction override attempts (`INJ_SYSTEM_OVERRIDE`, `INJ_SECURITY_DISABLE`).
    2. Indirect Prompt Injection: Scans docstrings and comments via `inspect_source_for_indirect_injections` and defuses injection text into `[DEFUSED_PROMPT_INJECTION]`, allowing valid code to proceed under `WARNING`.
    3. AST Policy Safety: Strictly blocks dangerous execution primitives (`eval`, `exec`, `os.system`, `subprocess`).
    4. Categorization: Distinguishes confirmed violations (`BLOCK`, `status="BLOCKED"|"REFUSED"`) from potential risks (`WARN`, `status="WARNING"`) and clean algorithms (`SAFE`, `status="PASSED"`).
- **Contract:** Outputs validated [`SecurityEvaluationPayload`](file:///Users/sourabh/TestForge/testforge/a2a.py#L321).
- **Blackboard Updates:** Writes structured assessment findings, risk levels, and remediation notes to `SecuritySpace`.

---

## 2. Actual Workflow Integration

In [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py):
1. **Agent Instantiation & A2A Registration (`__init__`):**
   - Instantiates `self.code_intel_agent` and `self.security_agent`.
   - Registers handlers with `self.broker`:
     - `"agent:google-adk:code-intelligence"` -> `self.code_intel_agent.handle_a2a_message`
     - `"agent:google-adk:security"` -> `self.security_agent.handle_a2a_message`
2. **Step 0: Security Gatekeeping (`_execute_pipeline`):**
   - Invokes `self.security_agent.evaluate_source(...)`.
   - If `allowed == False`, dispatches `SECURITY_REFUSAL` lifecycle event, logs refusal, sets `self.state.final_hardening_status = "FAILED"`, and halts immediately.
   - If allowed, attaches `security_assessment` to `self.state.metadata`.
3. **Step 1: Code Intelligence & Symbol Ingestion (`_execute_pipeline`):**
   - Invokes `self.code_intel_agent.analyze_source(...)`.
   - Commits branches, exceptions, call graphs, and boundary conditions to `TargetSpace` and `PlanSpace`.
   - Emits `AGENT_HANDOFF` event from `SecurityAgent` to `CodeIntelligenceAgent`.
   - Preserves `TargetManagerAgent` to `TestGeneratorAgent` handoff for backward compatibility.
   - Attaches `code_intelligence` to `self.state.metadata`.

---

## 3. Observability & Telemetry

- **Lifecycle Events Dispatched:** `OPERATION_START`, `SECURITY_REFUSAL`, and `OPERATION_COMPLETE` for both agents.
- **Trace Logger Invocations:** Every analysis and evaluation run is recorded in `testforge_trace.jsonl` under `AGENT_EXECUTION` with agent name, framework (`Google ADK`), job ID, status, and duration.
- **Wiretap Dashboard (`server.py`):** `/api/wiretap` advertises both `CodeIntelligenceAgent` and `SecurityAgent` in `registered_agents` and derives active agents dynamically from logged handoffs.

---

## 4. Test Verification Evidence

### 4.1 Focused Test Suite (21 Tests, 100% Passed)

Command:
```bash
.venv-release/bin/python3 -m pytest tests/test_code_intelligence_agent.py tests/test_security_agent.py tests/test_phase3_workflow_integration.py -v
```

Output:
```
============================= test session starts ==============================
platform darwin -- Python 3.13.18, pytest-9.1.1, pluggy-1.7.0 -- /Users/sourabh/TestForge/.venv-release/bin/python3
cachedir: .pytest_cache
rootdir: /Users/sourabh/TestForge
plugins: cov-7.1.0, anyio-4.15.1, platformdirs-4.13.5
collecting ... collected 21 items

tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_function_and_class_extraction PASSED [  4%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_branch_identification PASSED [  9%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_exception_path_identification PASSED [ 14%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_dependency_extraction PASSED [ 19%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_invalid_python_source PASSED [ 23%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_empty_source PASSED [ 28%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_structured_output_validation PASSED [ 33%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_blackboard_publication PASSED [ 38%]
tests/test_code_intelligence_agent.py::TestCodeIntelligenceAgent::test_a2a_communication PASSED [ 42%]
tests/test_security_agent.py::TestSecurityAgent::test_safe_source_code_cleared PASSED [ 47%]
tests/test_security_agent.py::TestSecurityAgent::test_suspicious_source_code_handling PASSED [ 52%]
tests/test_security_agent.py::TestSecurityAgent::test_blocking_os_system_violation PASSED [ 57%]
tests/test_security_agent.py::TestSecurityAgent::test_blocking_eval_violation PASSED [ 61%]
tests/test_security_agent.py::TestSecurityAgent::test_prompt_injection_refusal PASSED [ 66%]
tests/test_security_agent.py::TestSecurityAgent::test_secret_redaction PASSED [ 71%]
tests/test_security_agent.py::TestSecurityAgent::test_severity_classification PASSED [ 76%]
tests/test_security_agent.py::TestSecurityAgent::test_structured_output_validation PASSED [ 80%]
tests/test_security_agent.py::TestSecurityAgent::test_blackboard_publication PASSED [ 85%]
tests/test_security_agent.py::TestSecurityAgent::test_a2a_communication PASSED [ 90%]
tests/test_phase3_workflow_integration.py::TestPhase3WorkflowIntegration::test_workflow_invokes_both_agents_and_persists_outputs PASSED [ 95%]
tests/test_phase3_workflow_integration.py::TestPhase3WorkflowIntegration::test_workflow_security_refusal_on_policy_violation PASSED [100%]

======================= 21 passed, 7 warnings in 13.73s ========================
```

### 4.2 Full Regression Test Suite (675 Tests, 100% Passed)

Command:
```bash
.venv-release/bin/python3 -m pytest tests/ -q
```

Output:
```
675 passed, 348 warnings in 356.13s (0:05:56)
```

- **Total Tests Collected:** 675 (increased from 654 in Phase 2)
- **Total Tests Passed:** 675 (100%)
- **Total Tests Failed:** 0
- **Duration:** 356.13s
- **Regressions Introduced:** 0

---

## 5. Warnings Analysis

The 348 captured warnings originate from external library deprecations and are identical in nature to Phase 2:
1. `crewai/agent/core.py` and `crewai/crew.py`: Deprecation warnings regarding `function_calling_llm` and `allow_code_execution`.
2. `google/cloud/aiplatform/models.py`: Upstream notice regarding `google-cloud-storage < 3.0.0`.
3. `starlette/testclient.py`: Deprecation warning regarding `anyio.abc.BlockingPortal`.
4. `testforge/agents.py:543`: Pytest warning attempting to collect `TestGeneratorAgent` (legacy agent class). All newly introduced models (`CodeIntelligencePayload`, `SecurityEvaluationPayload`) are protected with `__test__ = False` and produce zero warnings.

---

## 6. Code Integrity Confirmation

- **Scope Adherence:** Only `CodeIntelligenceAgent` and `SecurityAgent` were implemented in this phase.
- **No Premature Implementation:** Supervisor Agent, Test Planning Agent, Test Execution Agent, and Reflection & Repair Agent were NOT implemented.
- **Orchestrator Architecture Preserved:** `TestForgeOrchestrator` remains the central workflow coordinator.
- **Historical Data Preserved:** No databases, trace files, benchmark results, or QA artifacts were modified or deleted.
- **Git State:** Zero git commits, pushes, cleans, or resets were performed.

---

## 7. Recommendation for Phase 4

With static analysis and continuous security screening firmly established as Google ADK agents, we are ready to proceed with **Phase 4: Planning & Execution Agent Realization**:
- Implement `TestPlanningAgent` (Google ADK) consuming `CodeIntelligencePayload` and emitting `TestPlanPayload`.
- Implement `TestExecutionAgent` (Google ADK + FastMCP/Sandbox) wrapping `ParallelSandboxRunner` to emit `TestExecutionPayload` and manage test isolation, pass@1 verification, and coverage collection.

