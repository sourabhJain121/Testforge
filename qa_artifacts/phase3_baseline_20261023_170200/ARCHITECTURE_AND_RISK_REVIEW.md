# TestForge — Phase 3 Architecture and Technical Risk Review

**Audit Directory:** `qa_artifacts/phase3_baseline_20261023_170200/`  
**Execution Timestamp:** 2026-10-23T17:03:00+05:30  
**Target Repository:** `/Users/sourabh/TestForge`  
**Author:** Senior Agentic AI Systems Architect  

---

## 1. Architectural Architecture Overview

TestForge is structured as a modular, decoupled, event-driven agentic testing platform. Its primary subsystems are organized as follows:

```
+-----------------------------------------------------------------------------------+
|                               USER INTERFACE LAYER                                |
|  - Cyber-Dark HUD (HTML5 / Vanilla CSS3 / ES6+ JavaScript)                        |
|  - Real-Time WebSocket Wiretap Feed (Live Event Cards)                           |
|  - Checkpoints Inspector & Semantic AST Diff Viewer                               |
|  - MCP Tools Status Modal & A2A Discovery Modal                                   |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / WebSockets
+-----------------------------------------v-----------------------------------------+
|                              FASTAPI BACKEND SERVER                               |
|  - REST Endpoints (/api/ingest, /api/harden, /api/checkpoints, /api/mcp/status)  |
|  - Discovery Services (/.well-known/agent-card.json, /.well-known/agent.json)     |
|  - WebSocket Hub (/ws/events with bounded queue & polling fallback)               |
|  - Health & Readiness Probes (/healthz, /readyz, /api/ready)                      |
+--------------------+------------------------------------+-------------------------+
                     |                                    |
+--------------------v--------------------+ +-------------v-------------------------+
|       MULTI-AGENT ORCHESTRATION         | |           SHARED STATE LAYER          |
| - CrewAI Adversarial Critic (Sequential)| | - Blackboard (5 Typed Partitions)     |
| - Google ADK Test Generator (LlmAgent)  | |   * TargetSpace, MutantSpace,         |
| - In-Process A2A Messaging Broker       | |     CriticSpace, SuiteSpace, Metrics  |
| - FastMCP Tool Provider & Client Manager| | - Thread-Safe Locks (threading.RLock) |
| - Pydantic Output Enforcement           | | - Monotonic Revision Tracking         |
+--------------------+--------------------+ +-------------+-------------------------+
                     |                                    |
+--------------------v--------------------+ +-------------v-------------------------+
|     EXECUTION & MUTATION ENGINE         | |     PERSISTENCE & OBSERVABILITY       |
| - Deterministic AST Mutator (AOR, ROR,  | | - SQLite Checkpoint Storage (testforge|
|   LCR, UOI, COD operators)              | | - TraceLogger (testforge_trace.jsonl) |
| - Parallel ProcessPool Sandbox Runner   | | - Provenance Chain Reconstructor      |
| - Resource Limits (RLIMIT_AS, Timeout)  | | - Multi-Run Benchmarking & Rate Card  |
| - Security Guardrails (AST, SSRF, RegEx)| | - Secret Redaction Filter             |
+-----------------------------------------+ +---------------------------------------+
```

---

## 2. Technical Risk Analysis & Prioritized Mitigations

### Risk 1: Unformalized Task Lifecycle Transitions
- **Current State:** Tasks transition through server handler steps (`INITIALIZING`, `RUNNING`, `HARDENED`, `FAILED`), but lack a formalized, stateful task finite state machine (FSM).
- **Risk Level:** **HIGH** (Can lead to race conditions during rapid retries or concurrent task execution).
- **Mitigation (Phase 1 / GAP-01):** Establish canonical task lifecycle:
  `CREATED -> VALIDATING -> INGESTING -> PLANNING -> GENERATING_TESTS -> EXECUTING -> MUTATION_ANALYSIS -> EVALUATING -> COMPLETED` (with `FAILED`, `CANCELLED`, `TIMED_OUT`, `RECOVERING`).

### Risk 2: Disconnected MCP Tool Invocation in Agent Planning
- **Current State:** FastMCP servers and client are fully implemented, verified across 18 tests, and surfaced in the UI modal, but the agent generator does not dynamically call the MCP client during runtime code generation.
- **Risk Level:** **HIGH** (Examiner may note that while MCP is verified, it is not actively driving the autonomous generation loop).
- **Mitigation (Phase 1 / GAP-02):** Wire the `MCPClientManager` into the orchestrator planning phase so that target file inspection and workspace metadata retrieval occur via real FastMCP tool invocations.

### Risk 3: Task Interruption without Automatic Resumption
- **Current State:** SQLite checkpoints preserve snapshots and allow manual UI restoration, but an interrupted hardening job does not automatically resume from the latest valid checkpoint.
- **Risk Level:** **HIGH** (Vital for production resilience and demonstrability during viva interruption scenarios).
- **Mitigation (Phase 1 / GAP-03):** Implement deterministic checkpoint resumption that checks for in-flight checkpoints upon task start and resumes without repeating previously evaluated mutants.

### Risk 4: Evaluation Corpus Narrowness
- **Current State:** Most test cases and demos rely on `discount.py` and `banking.py`.
- **Risk Level:** **MEDIUM to HIGH** (Evaluators may question generalizability across diverse control flow patterns).
- **Mitigation (Phase 2 / GAP-04):** Assemble a structured evaluation corpus including branching state machines (`samples/state_machine.py`), rate limiters (`samples/rate_limiter.py`), and inventory pricing logic, with documented defect manifests.

### Risk 5: Stochastic LLM Output & Offline Benchmark Transparency
- **Current State:** Real LLM generation is non-deterministic, while `--fast` offline mode uses deterministic fixtures.
- **Risk Level:** **MEDIUM** (Misrepresenting simulated metrics as live foundation model performance would violate academic integrity).
- **Mitigation (Phase 2 / GAP-05):** Maintain strict metric taxonomy (`MEASURED`, `CALCULATED`, `ESTIMATED`, `UNKNOWN/UNAVAILABLE`), multi-run sample statistics ($N \ge 1$ with mean/stdev), and prominent offline simulation disclaimers.

### Risk 6: Sandbox Breakout from Untrusted Code
- **Current State:** The parallel sandbox relies on OS process limits (`RLIMIT_AS`), timeouts, and static AST parsing.
- **Risk Level:** **HIGH** (Untrusted code from GitHub imports or generative LLMs must not access host credentials or network).
- **Mitigation (Phase 3 / GAP-06):** Reinforce security visitor with negative test matrix covering docstring prompt injection, indirect eval aliasing, SSRF private IP targets, and memory exhaustion.

### Risk 7: Live Viva Demonstration Brittleness
- **Current State:** Demonstrating live cloud LLMs in an academic viva is vulnerable to WiFi dropouts, API rate limits, or slow response times.
- **Risk Level:** **HIGH** (Can undermine an otherwise excellent technical demonstration).
- **Mitigation (Phase 5 / GAP-09):** Package a deterministic, local evaluation fixture with known defects, allowing a 100% offline, reproducible 5-minute evaluator demonstration.
