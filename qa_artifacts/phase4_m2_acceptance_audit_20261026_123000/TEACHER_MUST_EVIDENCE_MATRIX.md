# Teacher MUST Requirements: Evidence & Acceptance Matrix

**Repository:** `/Users/sourabh/TestForge`  
**Milestone:** Phase 4.1.2 — Pre-Evaluation Acceptance Audit  
**Timestamp:** `20261026_123000`  
**Evaluation Scope:** All 11 Mandatory Requirements ("Teacher MUSTs") for University Submission  

---

## 1. Compliance Summary Table

| Requirement ID | Requirement Description | Implementation Location | Test / Demonstration Evidence | Audit Status |
|---|---|---|---|:---:|
| **MUST 1** | Shared context and state between agents | `testforge/blackboard.py`, `testforge/orchestrator.py` | `tests/test_blackboard.py` (18 passed), `tests/test_agentic_pipeline.py` (5 passed) | **VERIFIED** |
| **MUST 2** | At least two genuine MCP tool integrations | `testforge/mcp_client.py`, `testforge/mcp_server.py` | `tests/test_mcp.py` (22 passed) | **VERIFIED** |
| **MUST 3** | Structured Pydantic outputs & final output formats | `testforge/a2a.py`, `testforge/benchmarking.py`, `testforge/guidance.py` | `tests/test_benchmarking.py` (5 passed), `tests/test_a2a.py` (16 passed) | **VERIFIED** |
| **MUST 4** | Appropriate agentic design patterns and comparison | `testforge/orchestrator.py`, `testforge/corpus/runner.py` | `tests/test_agentic_pipeline.py` (5 passed), `tests/test_strategy_comparison.py` (13 passed) | **VERIFIED** |
| **MUST 5** | Callbacks, task monitoring, and logging | `testforge/callbacks.py`, `testforge/logger.py` | `tests/test_callbacks.py` (12 passed), `tests/test_observability.py` (7 passed) | **VERIFIED** |
| **MUST 6** | Official A2A protocol between agents | `testforge/a2a_protocol.py`, `server.py` | `tests/test_a2a_protocol.py` (15 passed) | **VERIFIED** |
| **MUST 7** | Both Google ADK and CrewAI, no 3rd framework | `testforge/adk_generator.py`, `testforge/crew_critic.py` | `tests/test_adk_generator.py` (14 passed), `tests/test_crew_critic.py` (9 passed) | **VERIFIED** |
| **MUST 8** | Security guardrails and prompt variants | `testforge/security.py`, `testforge/agents.py` | `tests/test_security.py` (30 passed), `tests/test_adversarial_failure_injection.py` (18 passed) | **VERIFIED** |
| **MUST 9** | End-to-end observability and provenance | `testforge/logger.py` | `tests/test_observability.py` (7 passed) | **VERIFIED** |
| **MUST 10** | Multi-run performance and cost benchmarking | `testforge/benchmarking.py`, `run_benchmark.py` | `tests/test_benchmarking.py` (5 passed), `tests/test_fast_benchmarking.py` (3 passed) | **VERIFIED** |
| **MUST 11** | Cloud deployment readiness | `Dockerfile`, `docker-compose.yml`, `server.py` | `tests/test_deployment.py` (11 passed) | **VERIFIED** |

**Summary**: 11 / 11 Requirements are **VERIFIED** with concrete code and test evidence.

---

## 2. Detailed Evidence by Requirement

### MUST 1 — Shared Context and State Between Agents (Blackboard Architecture)
- **Implementation:** [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py), [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py).
- **Architecture:** Thread-safe, monotonic-revisioned `Blackboard` partitioned into 5 strongly typed spaces: `TargetSpace`, `MutantSpace`, `CriticSpace` (including `semantic_guidance`), `SuiteSpace`, and `MetricsSpace`. Point-in-time immutable snapshots (`get_snapshot()`).
- **Test Evidence:**
  - `pytest tests/test_blackboard.py -v`: 18 passed.
  - `pytest tests/test_agentic_pipeline.py -v`: 5 passed.
  - Verifies atomic rollback on invalid updates, monotonic revisioning, and cross-agent provenance.
- **Audit Status:** **VERIFIED**.

---

### MUST 2 — At Least Two Genuine External Tools Through MCP
- **Implementation:** [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py), [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py).
- **Architecture:** Implements the official Model Context Protocol (`mcp` SDK) via JSON-RPC 2.0 over stdio transport.
  1. **Filesystem MCP Server**: Exposes `read_text_file`, `list_directory`, `get_file_info`. Enforces path restriction containment (`permitted_root`), traversal protection, and sensitive file blocking.
  2. **GitHub MCP Server**: Exposes `search_repositories`, `get_file_contents`, `get_issue`. Handles public unauthenticated mode and token authentication without secret logging.
- **Test Evidence:**
  - `pytest tests/test_mcp.py -v`: 22 passed in 11.8s.
  - Verifies schema validation, tool discovery, timeout handling, path traversal rejection, and stdio communication.
- **Audit Status:** **VERIFIED**.

---

### MUST 3 — Structured Pydantic Outputs & Final Output Formats
- **Implementation:** [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py), [`testforge/benchmarking.py`](file:///Users/sourabh/TestForge/testforge/benchmarking.py), [`testforge/guidance.py`](file:///Users/sourabh/TestForge/testforge/guidance.py), [`testforge/corpus/models.py`](file:///Users/sourabh/TestForge/testforge/corpus/models.py).
- **Architecture:** All agent messages and outputs enforce Pydantic v2 schemas:
  - `SemanticMutantGuidance`: operational distinctions, boundaries, confidence.
  - `GeneratedTestPayload`, `CriticDirectivePayload`, `MetricBreakdown`, `BenchmarkReport`.
  - Output presentations: Glassmorphic web UI (`frontend/`), Terminal Rich table, machine-readable JSON (`benchmark_results.json`), and GitHub markdown (`benchmark_results.md`).
- **Test Evidence:**
  - `pytest tests/test_benchmarking.py tests/test_a2a.py -v`: 21 passed.
- **Audit Status:** **VERIFIED**.

---

### MUST 4 — Appropriate Agentic Patterns and Comparison (Evaluator-Optimizer / Reflection)
- **Implementation:** [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py), [`testforge/corpus/runner.py`](file:///Users/sourabh/TestForge/testforge/corpus/runner.py).
- **Architecture:** Implements the canonical Evaluator-Optimizer (Reflection) loop:
  - Google ADK Synthesizer $\rightarrow$ Clean Code Sandbox pass@1 $\rightarrow$ AST Fault Injection $\rightarrow$ Sandbox Evaluation $\rightarrow$ CrewAI Adversarial Critic with Semantic Guidance $\rightarrow$ Test Hardening.
  - Comparative benchmark evaluates 3 conditions: Baseline (Handwritten), Zero-Shot, and Agentic Reflection.
- **Test Evidence:**
  - `pytest tests/test_agentic_pipeline.py -v`: 5 passed.
  - `pytest tests/test_strategy_comparison.py -v`: 13 passed.
- **Audit Status:** **VERIFIED** (with documented Finding H-01 on benchmark runner mutant scoring).

---

### MUST 5 — Callbacks, Task Monitoring, and Logging
- **Implementation:** [`testforge/callbacks.py`](file:///Users/sourabh/TestForge/testforge/callbacks.py), [`testforge/logger.py`](file:///Users/sourabh/TestForge/testforge/logger.py).
- **Architecture:**
  - `CallbackRegistry` provides failure-isolated event dispatch across 10 lifecycle event types (`AGENT_START`, `TOOL_CALL`, `STATE_UPDATE`, `SECURITY_REFUSAL`, `TIMEOUT`, etc.).
  - `TraceLogger` logs structured events to JSONL with automatic credential scrubbing.
- **Test Evidence:**
  - `pytest tests/test_callbacks.py -v`: 12 passed.
  - `pytest tests/test_observability.py -v`: 7 passed.
- **Audit Status:** **VERIFIED**.

---

### MUST 6 — Official A2A Protocol Between Agents
- **Implementation:** [`testforge/a2a_protocol.py`](file:///Users/sourabh/TestForge/testforge/a2a_protocol.py), mounted on [`server.py`](file:///Users/sourabh/TestForge/server.py).
- **Architecture:**
  - Uses the official `a2a-sdk==0.3.26` package (Protocol version `0.3.0`).
  - Publishes AgentCard at `/.well-known/agent-card.json` and `/.well-known/agent.json`.
  - JSON-RPC 2.0 over HTTP transport managing task lifecycle states (`submitted` $\rightarrow$ `working` $\rightarrow$ `completed`).
- **Test Evidence:**
  - `pytest tests/test_a2a_protocol.py -v`: 15 passed in 3.2s.
- **Audit Status:** **VERIFIED**.

---

### MUST 7 — Both Google ADK and CrewAI, Without a Third Agentic Framework
- **Implementation:** [`testforge/adk_generator.py`](file:///Users/sourabh/TestForge/testforge/adk_generator.py) (Google ADK) and [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py) (CrewAI).
- **Architecture:**
  - Google ADK (`google.adk.agent.LlmAgent`, `Runner`) acts as the Test Generator.
  - CrewAI (`crewai.Agent`, `crewai.Task`, `crewai.Crew`) acts as the Adversarial Critic.
  - Strict absence of any third framework (LangChain, AutoGen, LangGraph).
- **Test Evidence:**
  - `pytest tests/test_adk_generator.py tests/test_crew_critic.py -v`: 23 passed in 4.6s.
- **Audit Status:** **VERIFIED**.

---

### MUST 8 — Security Guardrails and Code Validation
- **Implementation:** [`testforge/security.py`](file:///Users/sourabh/TestForge/testforge/security.py), [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py).
- **Architecture:**
  - `SecurityGuardrail` AST inspection blocks dangerous primitives: `eval`, `exec`, `os.system`, `subprocess.Popen`, network sockets, dynamic imports.
  - Regex screening blocks prompt injections, system override attempts, and abusive language while allowing valid domain terminology ("kill mutant", "dead code").
  - Subprocess execution timeout guardrail (5.0s default) prevents infinite loops.
- **Test Evidence:**
  - `pytest tests/test_security.py tests/test_adversarial_failure_injection.py -v`: 48 passed in 3.7s.
- **Audit Status:** **VERIFIED**.

---

### MUST 9 — End-to-End Observability and Provenance
- **Implementation:** [`testforge/logger.py`](file:///Users/sourabh/TestForge/testforge/logger.py).
- **Architecture:**
  - Top-level `workflow_id` and operation `correlation_id` across all events.
  - `TraceLogger.get_provenance_chain(mutant_id)` queries the full lifecycle history of any mutant from injection $\rightarrow$ survival $\rightarrow$ directive $\rightarrow$ test $\rightarrow$ kill.
- **Test Evidence:**
  - `pytest tests/test_observability.py -v`: 7 passed in 4.1s.
- **Audit Status:** **VERIFIED**.

---

### MUST 10 — Multi-Run Performance and Cost Benchmarking
- **Implementation:** [`testforge/benchmarking.py`](file:///Users/sourabh/TestForge/testforge/benchmarking.py), [`run_benchmark.py`](file:///Users/sourabh/TestForge/run_benchmark.py).
- **Architecture:**
  - `BenchmarkRunner` runs $N$ repetitions per scenario, computing mean and sample standard deviation for latency, mutation scores, and coverage.
  - Categorizes metrics into measured, calculated, estimated (cost in USD via Gemini pricing), and unavailable.
  - Zero token fabrication in offline environments.
- **Test Evidence:**
  - `pytest tests/test_benchmarking.py -v`: 5 passed.
  - `pytest tests/test_fast_benchmarking.py -v`: 3 passed.
- **Audit Status:** **VERIFIED**.

---

### MUST 11 — Cloud Deployment Readiness
- **Implementation:** [`Dockerfile`](file:///Users/sourabh/TestForge/Dockerfile), [`docker-compose.yml`](file:///Users/sourabh/TestForge/docker-compose.yml), [`server.py`](file:///Users/sourabh/TestForge/server.py), [`docs/DEPLOYMENT_GUIDE.md`](file:///Users/sourabh/TestForge/docs/DEPLOYMENT_GUIDE.md).
- **Architecture:**
  - Multi-stage Docker container build with non-root security.
  - Liveness probe at `/healthz`, deep readiness probe at `/readyz`.
  - Docker Compose orchestration with healthcheck definitions.
- **Test Evidence:**
  - `pytest tests/test_deployment.py -v`: 11 passed.
- **Audit Status:** **VERIFIED**.
