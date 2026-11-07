# Eight-Agent Architecture Mapping & Role Boundaries

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT & ARCHITECTURAL PROPOSAL COMPLETED  

---

## 1. Architectural Principles of the 8-Agent System

To elevate TestForge from a procedural pipeline with specialist agent adapters to a **cohesive, modular 8-agent cognitive architecture**, the following core design invariants are established:

1. **Google ADK as the Primary Orchestration Framework:**
   Google ADK (`google.adk`) provides the top-level orchestration topology using official ADK workflow patterns (`SequentialAgent`, `LoopAgent`, or an ADK `Supervisor` with delegated subordinate agents via `Runner` and session context).
2. **CrewAI as a Bounded Specialist Critic:**
   CrewAI (`crewai`) is NOT a competing top-level orchestrator. It is scoped strictly to the **Mutation & Quality Critic Agent**, functioning as a specialized analytical agent invoked under the ADK workflow through typed A2A contracts.
3. **Blackboard as Shared Context & State Broker:**
   No peer-to-peer data leaking. All inter-agent data flow transitions through typed, thread-safe Blackboard partitions (`TargetSpace`, `PlanSpace`, `SuiteSpace`, `ExecutionSpace`, `MutantSpace`, `CriticSpace`, `SecuritySpace`, `MetricsSpace`).
4. **Pydantic Contracts for Every Handoff:**
   Every input and output between agents is validated by strict, fail-closed Pydantic v2 schemas.
5. **Controlled Tool Access via FastMCP & Python Sandboxing:**
   Tools (filesystem, GitHub, AST mutator, pytest sandbox) are governed by MCP interfaces and executed under strict least-privilege security policies.

---

## 2. Comprehensive 8-Agent Mapping Table

| # | Proposed Agent | Recommended Framework | Existing Component to Reuse | Missing Work Required | Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Supervisor Agent** | **Google ADK**<br>(`LlmAgent` + `Runner` + `InMemorySessionService`) | `SupervisorAgent` in [`testforge/supervisor_agent.py`](file:///Users/sourabh/TestForge/testforge/supervisor_agent.py) | **COMPLETED & VERIFIED (Phase 7)**: Authoritative multi-agent supervisor. Manages DAG workflow transitions, validates state changes, strictly enforces deterministic policies over LLM reasoning, tracks live agent status for wiretap, and synchronizes decisions to Blackboard. | Blackboard, CallbackRegistry, SQLite/TraceLogger |
| **2** | **Code Intelligence Agent** | **Google ADK + Python AST**<br>(`LlmAgent` + Function Tools) | `TargetManagerAgent.ingest_file` ([`ingestion.py:375`](file:///Users/sourabh/TestForge/testforge/ingestion.py#L375)), `BlastRadiusAnalyzer` ([`blast_analyzer.py:45`](file:///Users/sourabh/TestForge/testforge/blast_analyzer.py#L45)), `extract_function_signatures` ([`agents.py:72`](file:///Users/sourabh/TestForge/testforge/agents.py#L72)) | **COMPLETED & VERIFIED (Phase 3)**: Implemented in [`testforge/code_intelligence_agent.py`](file:///Users/sourabh/TestForge/testforge/code_intelligence_agent.py). Extracts branches, exceptions, complexity, call graphs; emits `CodeIntelligencePayload`. | FastMCP Filesystem Server, Python `ast` |
| **3** | **Test Planning Agent** | **Google ADK**<br>(`LlmAgent` + Pydantic schema) | `intelligent_generator.py` callable analysis, boundary condition heuristics from `guidance.py` | **COMPLETED & VERIFIED (Phase 4)**: Implemented in [`testforge/planning_agent.py`](file:///Users/sourabh/TestForge/testforge/planning_agent.py). Formulates nominal, boundary, negative, exception scenarios with McCabe prioritization and deduplication; emits `TestPlanPayload`. | Code Intelligence Agent output (`TargetSpace`) |
| **4** | **Test Generation Agent** | **Google ADK + LLM**<br>(`LlmAgent` + `Runner`) | `GoogleADKTestGenerator` ([`adk_generator.py:330`](file:///Users/sourabh/TestForge/testforge/adk_generator.py#L330)), `intelligent_generator.py` assertion synthesizer | **COMPLETED & VERIFIED (Phases 1-7)**: Operational in `adk_crewai` mode, coordinated by Supervisor Agent via `SupervisorAction.GENERATE_TESTS`. Focuses on initial test synthesis, fixture generation, and clean executable test structure. | Test Planning Agent output (`PlanSpace`), `HybridLLMClient` |
| **5** | **Test Execution Agent** | **Google ADK + MCP Tools**<br>(`LlmAgent` + MCP / Sandbox) | `ParallelSandboxRunner` ([`sandbox.py:196`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L196)), `GranularTestValidator` ([`sandbox.py:429`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L429)), `MCPClientManager` ([`mcp_client.py:146`](file:///Users/sourabh/TestForge/testforge/mcp_client.py#L146)) | **COMPLETED & VERIFIED (Phase 4)**: Implemented in [`testforge/execution_agent.py`](file:///Users/sourabh/TestForge/testforge/execution_agent.py). Coordinates isolated subprocess execution, pass@1 validation, pytest-cov coverage, and parallel mutant evaluation; emits `TestExecutionPayload`. | Sandbox process pool, `pytest-cov`, `SuiteSpace` |
| **6** | **Mutation & Quality Critic Agent** | **CrewAI**<br>(`Agent` + `Task` + `Crew`) | `MutationQualityCriticAgent` / `CrewAICriticAgent` ([`crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py)), `TestQualityAnalyzer` | **COMPLETED & VERIFIED (Phase 5)**: Implemented dual mutation & test quality critique in [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py). Consumes real mutant execution results without fabrication, performs AST assertion quality analysis (weak assertions, tautologies, missing boundaries), and emits `MutationQualityCriticPayload`. | Test Execution Agent output (`ExecutionSpace`), `MutantSpace`, `CriticSpace` |
| **7** | **Security Agent** | **Google ADK**<br>(`LlmAgent` + AST Visitor Tools) | `SecurityGuardrail` ([`security.py:239`](file:///Users/sourabh/TestForge/testforge/security.py#L239)), `CodeSanitizer` ([`agents.py:227`](file:///Users/sourabh/TestForge/testforge/agents.py#L227)), `prompt_guard.py` indirect injection defenses | **COMPLETED & VERIFIED (Phase 3)**: Implemented in [`testforge/security_agent.py`](file:///Users/sourabh/TestForge/testforge/security_agent.py). Multi-layer guardrails, prompt injection defusing, AST policy gatekeeper; emits `SecurityEvaluationPayload`. | Python `ast`, FastMCP security policies |
| **8** | **Reflection & Repair Agent** | **Google ADK**<br>(`LlmAgent` + `Runner`) | `ReflectionRepairAgent` in [`testforge/reflection_agent.py`](file:///Users/sourabh/TestForge/testforge/reflection_agent.py), reflection loop in `orchestrator.py:1330` | **COMPLETED & VERIFIED (Phase 6)**: Implemented in [`testforge/reflection_agent.py`](file:///Users/sourabh/TestForge/testforge/reflection_agent.py) with Google ADK (`LlmAgent`, `Runner`, `InMemorySessionService`, `ReflectionModelBridge`). Synthesizes targeted discriminating assertions based on execution failures and surviving mutant diffs, coordinates clean validation with strict non-regression verification, and emits `RepairDirectivePayload`, `RepairResultPayload`, and `ReflectionDecisionPayload`. | Critic output (`CriticSpace`), Execution results (`ExecutionSpace`), `SuiteSpace` |

---

## 3. Detailed Agent Specifications & Cognitive Boundaries

```
+----------------------------------------------------------------------------------------------------+
|                                    SUPERVISOR AGENT (Google ADK)                                   |
|   Controls global convergence criteria, budget limits, loop transitions, and Blackboard snapshots  |
+----------------------------------------------------------------------------------------------------+
                                                  |
           +--------------------------------------+--------------------------------------+
           |                                      |                                      |
           v                                      v                                      v
+------------------------+             +------------------------+             +----------------------+
| CODE INTELLIGENCE AGENT|             |    TEST PLANNING AGENT |             |    SECURITY AGENT    |
|  (Google ADK + AST)    |             |      (Google ADK)      |             |     (Google ADK)     |
| AST extraction, call   |             | Scenario partition,    |             | Input screening,     |
| graphs, blast radius,  |             | boundary definitions,  |             | generated code AST   |
| complexity analysis    |             | test budget plan       |             | safety, secret scrub |
+------------------------+             +------------------------+             +----------------------+
           |                                      |                                      |
           +--------------------------------------+--------------------------------------+
                                                  |
                                                  v
                               +------------------------------------+
                               |     TEST GENERATION AGENT (ADK)    |
                               | Baseline Pytest synthesis, value-  |
                               | aware assertions, nominal paths    |
                               +------------------------------------+
                                                  |
                                                  v
                               +------------------------------------+
                               |    TEST EXECUTION AGENT (ADK+MCP)  |
                               | Clean validation (pass@1), pytest- |
                               | cov coverage, failure triage       |
                               +------------------------------------+
                                                  |
                                                  v
                               +------------------------------------+
                               |  MUTATION & QUALITY CRITIC (CrewAI)|
                               | Deterministic AST mutation, score  |
                               | computation, surviving diff diag   |
                               +------------------------------------+
                                                  |
                    [Target Score Achieved? No]  |  [Target Score Achieved? Yes]
                    +-----------------------------+-----------------------------+
                    |                                                           |
                    v                                                           v
+------------------------------------+                         +----------------------------------+
|   REFLECTION & REPAIR AGENT (ADK)  |                         |        HARDENING COMPLETE        |
| Differential assertion synthesis,  |                         | Final hardened suite exported to |
| targeted mutant killing            |                         | SQLite & exported test file      |
+------------------------------------+                         +----------------------------------+
                    |
                    +------------> [Loop Back to Test Execution Agent]
```

### 3.1 What Makes Each Component Genuinely Agentic?

1. **Supervisor Agent (ADK):**
   - *Not just a loop:* Evaluates multi-dimensional stopping conditions (mutation score thresholds, line coverage plateau, token expenditure, timeout risk) and dynamically adjusts reflection strategy.
2. **Code Intelligence Agent (ADK + AST):**
   - *Not just `ast.parse`:* Actively reasons about code semantics, detects hidden side effects, identifies recursion/loops, and computes blast radius risk to formulate testing guidance.
3. **Test Planning Agent (ADK):**
   - *Not just template expansion:* Analyzes code structure to prioritize equivalence partitions, nominal vs. boundary vs. error-handling cases, and allocates test counts based on blast risk.
4. **Test Generation Agent (ADK + LLM):**
   - *Not just raw code prompting:* Follows the typed `TestPlanPayload`, applies defensive system instructions, formats nominal assertions using value-aware synthesis, and guarantees syntactic validity.
5. **Test Execution Agent (ADK + MCP Tools):**
   - *Not just `subprocess.run`:* Triages test outcomes, isolates individual failing assertions, removes quarantined or broken tests, detects flaky assertions, and computes line/branch coverage gaps.
6. **Mutation & Quality Critic Agent (CrewAI):**
   - *Not just a score calculator:* A bounded CrewAI specialist team (Auditor & Critic) analyzing surviving AST mutants, diagnosing unexercised logical branches, categorizing failure mechanisms, and issuing actionable adversarial directives.
7. **Security Agent (ADK):**
   - *Not just a regex filter:* Operates continuously across all agent handoffs. Enforces AST safety policies on generated code (banning unauthorized OS calls), defuses prompt injections in source docstrings/comments, and redacts sensitive credentials.
8. **Reflection & Repair Agent (ADK):**
   - *Not a repeat generation:* Synthesizes differential patches and targeted discriminating assertions explicitly engineered to kill specific surviving mutants identified by the Critic.

---

## 4. CrewAI Bounded Specialist Integration Pattern

To avoid dual orchestration or competing agent frameworks:
- **ADK Owns the Workflow:** The ADK Supervisor Agent controls when mutation evaluation and critique are needed.
- **A2A Contract Boundary:** The ADK Supervisor or Reflection coordinator dispatches an `A2AMessage(performative=REQUEST, action="critique_mutants")` with payload `A2ACritiqueRequestPayload` to the `agent:crewai:critic` registered handler.
- **CrewAI Internal Execution:** `CrewAICriticAgent` executes a self-contained Crew (`Agent` + `Task` + `Crew`) to deliberate over surviving mutants.
- **Typed Response Return:** Returns an `A2AMessage(performative=INFORM)` with payload `CriticDirectivePayload`.
- **Blackboard Sync:** The result is committed to `Blackboard.CriticSpace`. CrewAI never writes directly to other partitions or triggers subsequent workflow steps.

