# TestForge — Final Phase 2 Rubric Reconciliation & Evidence Integrity Audit

**Audit Directory:** `qa_artifacts/phase2_rubric_reconciliation_20261023_165500/`  
**Prior Reference Audits:**
- Initial MUST-Gap Audit: `qa_artifacts/phase2_must_gap_audit_20261023_160800/`
- Full Master Acceptance Audit: `qa_artifacts/phase2_master_acceptance_20261023_162200/`
**Authoritative Rubric Source:** `docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md` (*CSE3101 Autonomous Agentic Systems Rigorous Rubric*)  
**Execution Timestamp:** 2026-10-23T16:55:00+05:30  
**Evaluator Environment:** Python 3.13.17 (`.venv-release`), Node.js v24.15.0, Google Chrome 156.0.8078.48 via CDP, Docker Desktop 28.5.1  

---

## 1. Executive Summary & Rubric Discrepancy Resolution

### 1.1 The Identified Discrepancy
In the prior audit report (`qa_artifacts/phase2_master_acceptance_20261023_162200/FINAL_PHASE2_ACCEPTANCE_REPORT.md`), Section 8 and `REQUIREMENTS_TRACEABILITY_FINAL.csv` mapped requirements to specific application features (such as AST Ingestion Mode A, GitHub Ingestion Mode C, Parallel Sandbox, Mutation Engine, Checkpoints). 

While these represent vital engineering capabilities of TestForge, they inadvertently diverged from the canonical 11 MUST requirements originally established in `qa_artifacts/phase2_must_gap_audit_20261023_160800/MUST_GAP_MATRIX.csv` and authored in `docs/TESTFORGE_11_REQUIREMENTS_DEEP_AUDIT.md` (the official *CSE3101 Autonomous Agentic Systems Rigorous Rubric*).

### 1.2 The Resolution & Dual-Track Traceability
To ensure rigorous academic integrity and evaluation alignment, this audit **fully restores the canonical 11 MUST definitions as the authoritative evaluation standard**. The application-specific workflows are separated into an independent **Domain Application Capabilities Checklist**.

Both tracks have been independently audited, tested, and verified.

---

## 2. Deep-Dive Verification of the Canonical 11 MUST Requirements

### MUST-01: Shared Blackboard/State and Messaging Comparison
* **Rubric Requirement:** Multi-agent state coordination via a shared, partitioned blackboard with thread safety and snapshot isolation, alongside an architectural comparison against message-based broker dispatch.
* **Source Implementation:**
  - `testforge/blackboard.py`: `Blackboard` class featuring 5 typed partitions (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`), guarded by `threading.RLock()`, monotonic revision tracking, deep-copy snapshotting (`snapshot()`), and partition-filtered observer subscriptions.
  - `testforge/a2a.py`: `A2ABroker` providing decoupled in-process message dispatch supporting `A2AMessage` and `A2APerformative` (`REQUEST`, `INFORM`, `AGREE`, `REFUSE`, `FAILURE`, `PROPOSE`).
  - `testforge/benchmark_messaging.py`: Standalone micro-benchmark script comparing atomic partition mutation vs deep snapshotting vs A2A broker dispatch.
* **Test Verification:**
  - `tests/test_blackboard.py`: 18/18 passed.
  - `tests/test_blackboard_persistence.py`: 22/22 passed.
  - `tests/test_a2a.py`: 16/16 passed.
  - `tests/test_messaging_benchmark.py`: 5/5 passed.
* **Measured Benchmark Results (1,000 repetitions):**
  - **Blackboard In-Memory Partition Mutation:** 14.82 $\mu$s avg | 67,134 ops/sec.
  - **Blackboard Deep Snapshot Copy:** 26.55 $\mu$s avg | 36,948 ops/sec.
  - **In-Process A2A Broker Message Dispatch:** 107.66 $\mu$s avg | 8,673 ops/sec.
* **Demonstration:** Evaluators can inspect real-time Blackboard partition updates during Hardening Lab runs in Chrome, or run `python -m testforge.benchmark_messaging`.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-02: At Least Two Genuine MCP Tools
* **Rubric Requirement:** Implementation and verification of at least two genuine tools operating over the official Model Context Protocol (FastMCP) with input validation, confinement, and schema reflection.
* **Source Implementation:**
  - `testforge/mcp_server.py`: Built on official `FastMCP / mcp-python v1.28.0`.
    - **Server 1 (`testforge-filesystem`):**
      1. `read_text_file(path: str)`: Genuine text reading bounded by permitted root, blocking directory traversal (`../`), symlinks, and `.env`/credential patterns.
      2. `list_directory(path: str = ".")`: Directory entry enumeration with hidden/sensitive file masking.
      3. `get_file_info(path: str)`: File metadata, line count, and SHA-256 fingerprint generation.
    - **Server 2 (`testforge-github`):**
      4. `get_repository_info(owner: str, repo: str)`: Bounded public repository metadata retrieval with rate-limiting guardrails.
  - `testforge/mcp_client.py`: `MCPClientManager` using standard `mcp.client.stdio.stdio_client`.
  - `server.py`: Read-only `/api/mcp/status` exposing configured servers, registered tools count, and confinement policies.
  - `frontend/index.html` & `app.js`: `#btn-mcp-status` navbar pill and `#mcp-modal-backdrop` interactive introspection dialog.
* **Test Verification:**
  - `tests/test_mcp.py`: 16/16 passed (genuine stdio subprocess client connections, tool discovery, execution, path traversal rejection, credential redaction).
  - `tests/test_mcp_status_endpoint.py`: 2/2 passed (`/api/mcp/status` schema and `/api/ready` alias).
* **Demonstration:** Chrome CDP verified `#btn-mcp-status` tool count (`4`), `#mcp-modal` rendering, raw JSON link, and copy JSON feedback (`✅ Copied!`).
* **Status:** **END-TO-END VERIFIED**

---

### MUST-03: Pydantic Structured Outputs
* **Rubric Requirement:** Strict data schema enforcement across agent boundaries and task outputs using Pydantic `BaseModel` classes with fail-closed validation.
* **Source Implementation:**
  - `testforge/state.py`: `TestForgeState`, `MutantRecord`, `IterationMetrics`, `IngestionAnalysis`.
  - `testforge/a2a.py`: `CriticDirectivePayload`, `GeneratedTestPayload`, `A2ACritiqueRequestPayload`, `A2AMessage`.
  - `testforge/crew_critic.py`: Enforces `output_pydantic=CriticDirectivePayload` on CrewAI `Task`.
  - `testforge/adk_generator.py`: Enforces `output_schema=GeneratedTestPayload` on Google ADK `LlmAgent`.
  - `testforge/benchmarking.py`: `MetricBreakdown`, `BenchmarkReport`, `BenchmarkRunResult`.
  - `server.py`: `BlastRadiusPayload`, `GitDiffPayload`, `HardeningRunPayload`, `KeyConfigPayload`.
* **Validation Enforcement:** Zero untyped dictionary leakage across agent boundaries. Malformed LLM outputs trigger explicit `pydantic.ValidationError` caught by `CodeSanitizer`.
* **Test Verification:** Validated in `tests/test_crew_critic.py`, `tests/test_adk_generator.py`, `tests/test_agentic_pipeline.py`, and `tests/test_blackboard.py`.
* **Demonstration:** Inspected in browser Checkpoint raw JSON viewer, Telemetry trace rows, and Blast Radius KPI cards.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-04: Agentic-Pattern Comparison
* **Rubric Requirement:** Empirical multi-run benchmark comparing at least three distinct agentic architectures on identical target programs.
* **Source Implementation:**
  - `testforge/benchmarking.py` (`BenchmarkRunner`) and `run_benchmark.py`.
  - Compares 3 distinct strategies against `samples/discount.py`, `samples/banking.py`, `samples/inventory_pricing.py`, `samples/rate_limiter.py`, `samples/state_machine.py`:
    1. **Baseline Mode:** Static initial test generation without mutation or critic feedback.
    2. **Zero-Shot LLM Mode:** Direct single-pass LLM synthesis (`TestGeneratorAgent`).
    3. **Multi-Agent Reflection Loop Mode:** Iterative closed-loop pipeline (`TestForgeOrchestrator` combining ADK generator, CrewAI critic, and AST mutator).
* **Test Verification:**
  - `tests/test_benchmarking.py`: 12/12 passed.
  - `tests/test_fast_benchmarking.py`: 3/3 passed.
* **Live vs. Simulated Disclosure:**
  - **Live Mode:** Measures real LLM API wall-clock latency, tokens, and synthesized test code when `GEMINI_API_KEY` is present.
  - **Fast Offline Mode (`--fast`):** Uses deterministic mock fixtures for duration and mutation score to enable offline CI evaluation without API spend. The CLI and UI display a mandatory simulation disclosure banner.
* **Demonstration:** `python run_benchmark.py --fast -r 5` CLI; Chrome CDP tested Benchmark tab markdown view (CTRL-52 through CTRL-55).
* **Status:** **END-TO-END VERIFIED**

---

### MUST-05: Callbacks and Logging
* **Rubric Requirement:** Comprehensive lifecycle event auditing with sensitive data masking, asynchronous dispatch, and structured persistent storage.
* **Source Implementation:**
  - `testforge/callbacks.py`: `CallbackRegistry` supporting synchronous and asynchronous handlers across 18 typed `EventType` values (`OPERATION_START`, `STATE_CHANGE`, `A2A_MESSAGE`, `FAILOVER`, `SECURITY_REFUSAL`, etc.), priority ordering, error isolation, and recursive secret scrubbing (`_scrub_value`).
  - `testforge/logger.py`: `TraceLogger` streaming structured JSON records into `testforge_trace.jsonl` with correlation IDs.
  - `testforge/websocket_hub.py`: Bridges backend lifecycle callbacks to browser WebSocket clients.
* **Test Verification:**
  - `tests/test_callbacks.py`: 10/10 passed.
  - `tests/test_observability.py`: 14/14 passed.
  - `tests/test_websocket_hub.py`: 16/16 passed.
* **Demonstration:** Chrome CDP exercised the Wiretap event stream; simulated WebSocket disconnect verified immediate degradation to HTTP polling fallback (`/api/wiretap`).
* **Status:** **END-TO-END VERIFIED**

---

### MUST-06: A2A Discovery
* **Rubric Requirement:** Standardized machine-readable agent card discovery compliant with the Google Agent-to-Agent (A2A) protocol specification.
* **Source Implementation:**
  - `testforge/a2a_protocol.py`: Generates official A2A v0.3.0 `AgentCard` via `build_testforge_agent_card()`.
  - `server.py`: Exposes standard discovery endpoints at `/.well-known/agent-card.json` and alias `/.well-known/agent.json`.
  - `frontend/index.html` & `app.js`: `#btn-a2a-card` navbar button opens an interactive modal displaying agent capabilities, version, protocol, raw JSON link, and copy button.
* **Test Verification:**
  - `tests/test_a2a_protocol.py`: 18/18 passed.
  - `tests/test_a2a_card_ui_and_endpoint.py`: 17/17 passed.
  - `tests/test_deployment.py`: Passed.
* **Demonstration:** `curl http://127.0.0.1:8000/.well-known/agent-card.json`; Chrome CDP tested modal open, raw link, copy button with `✅ Copied!` transition, and Escape key dismissal (CTRL-17 through CTRL-21).
* **Status:** **END-TO-END VERIFIED**

---

### MUST-07: CrewAI + Google ADK Only (No Unapproved Frameworks)
* **Rubric Requirement:** Strict framework confinement restricting orchestration to CrewAI and Google ADK; total absence of unapproved frameworks (LangChain agents, AutoGen, LlamaIndex, Swarm).
* **Source Implementation:**
  - CrewAI: `testforge/crew_critic.py` uses `crewai.Agent(role='Adversarial QA Critic')`, `crewai.Task`, and `crewai.Crew(process=Process.sequential)` via `CrewAILLMBridge(BaseLLM)`.
  - Google ADK: `testforge/adk_generator.py` uses `google.adk.agents.llm_agent.LlmAgent`, `google.adk.runners.Runner`, `google.adk.sessions.in_memory_session_service.InMemorySessionService`, and `google.adk.models.base_llm.BaseLlm`.
  - Framework Confinement Audit: Codebase search across all files confirms zero imports of LangChain agents, AutoGen, LlamaIndex, or Swarm. `requirements.txt` specifies only `crewai`, `google-adk`, `google-genai`, `mcp`, and `a2a-sdk`.
* **Test Verification:**
  - `tests/test_crew_critic.py`: 20/20 passed.
  - `tests/test_adk_generator.py`: 24/24 passed.
* **Upstream Warnings Disclosure:** Upstream CrewAI 0.102.0 emits 208 deprecation warnings regarding upcoming Pydantic v2 argument migrations (`function_calling_llm`, `allow_code_execution`). These originate from the third-party package; 100% of tests pass.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-08: Security Guardrails and Prompt Variants
* **Rubric Requirement:** Fail-closed security guardrails against prompt injection and malicious code execution, paired with structured prompt engineering variants.
* **Source Implementation:**
  - `testforge/security.py`: `SecurityGuardrail` detects prompt injection attacks (`INJ_SYSTEM_OVERRIDE`, `INJ_NEW_ROLE_PROMPT`, `INJ_SECURITY_DISABLE`, `INJ_SYSTEM_DELIMITER_ESCAPE`, `INJ_SECRET_LEAK`).
  - AST Safety Inspection: Bounded visitor inspects Python AST and blocks dangerous primitives (`eval`, `exec`, `os.system`, `subprocess`, `__import__`, socket bindings).
  - Secret Redaction: `redact_sensitive_data` scrubs API keys and tokens before logging.
  - Mode C SSRF Protection: Blocks private RFC 1918 IPs, loopbacks, and cloud metadata endpoints (`169.254.169.254`).
  - Sandbox Isolation: `testforge/sandbox.py` executes test runs in isolated child subprocesses with memory limits (`RLIMIT_AS`), process timeouts, and temp directory boundaries.
  - Prompt Variants: Tailored prompt templates in `testforge/agents.py`.
* **Test Verification:**
  - `tests/test_security.py`: 30/30 passed.
  - `tests/test_adversarial_failure_injection.py`: 16/16 passed.
* **Demonstration:** Malicious code or injected prompts trigger immediate `SecurityRefusal` termination recorded in Wiretap.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-09: Observability and Provenance
* **Rubric Requirement:** End-to-end provenance linking every generated test artifact to its initiating mutant, line number, and critic directive with correlation ID chaining.
* **Source Implementation:**
  - `testforge/logger.py`: `TraceLogger` implements `get_provenance_chain(mutant_id)` querying lifecycle events from `MUTATION_GENERATED` to `SANDBOX_EVALUATED`, `CRITIC_DIRECTIVE`, and `HARDENED_EVALUATED`.
  - `get_audit_summary()` aggregates total events, correlation IDs, and security refusals.
  - Endpoints: `GET /api/telemetry` and `GET /api/wiretap`.
  - UI: Real-time Telemetry tab and Wiretap chronological timeline.
* **Test Verification:**
  - `tests/test_observability.py`: 14/14 passed.
  - `tests/test_agentic_pipeline.py`: 18/18 passed.
* **Demonstration:** Telemetry tab displays correlation IDs and token usage; Wiretap displays causal event timeline; `TraceLogger.get_provenance_chain(mutant_id)` reconstructs complete history.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-10: Multi-Run Performance and Cost Benchmarking
* **Rubric Requirement:** Reproducible statistical benchmarking across multiple runs with explicit separation of measured, calculated, and estimated cost metrics.
* **Source Implementation:**
  - `testforge/benchmarking.py` (`BenchmarkRunner`, `BenchmarkReport`, `MetricBreakdown`) and `run_benchmark.py`.
  - Strict Metric Classification:
    - **MEASURED:** Wall-clock duration, killed mutants, total mutants, iterations, tokens.
    - **CALCULATED:** Mutation score %, line coverage %.
    - **ESTIMATED:** Financial USD cost via published Gemini Flash pricing table ($0.075 input / $0.30 output per M tokens).
    - **UNKNOWN/UNAVAILABLE:** Explicitly tracked when telemetry is inaccessible.
  - Multi-run statistical aggregation ($N \ge 1$) calculating mean and sample standard deviation.
* **Test Verification:**
  - `tests/test_benchmarking.py`: 12/12 passed.
  - `tests/test_fast_benchmarking.py`: 3/3 passed.
* **Demonstration:** `python run_benchmark.py --fast -r 5` outputs Markdown and console table with variance metrics; Browser Benchmark tab renders formatted report.
* **Status:** **END-TO-END VERIFIED**

---

### MUST-11: Cloud Deployment Readiness
* **Rubric Requirement:** Production-ready containerization, orchestrator configuration, non-root execution, and liveness/readiness health probes.
* **Source Implementation:**
  - `Dockerfile`: Multi-stage Python 3.13-slim build, non-root user `testforge` (UID 1000), exposed port 8000, and built-in `HEALTHCHECK` targeting `/healthz`.
  - `docker-compose.yml`: Multi-service coordination on bridge network `testforge-net`.
  - Health Probes: `GET /healthz` (liveness), `GET /readyz` (readiness probing mutator, blackboard, persistence), and `GET /api/ready` alias.
* **Four-Level Verification Results:**
  1. **Level 1 (Compose Validation):** `docker compose config` passed with exit code 0.
  2. **Level 2 (Docker Image Build):** `docker build -t testforge:phase2-smoke .` succeeded with exit code 0 (`sha256:10139b558ccf...`).
  3. **Level 3 (Local Container Smoke Test):** Container `testforge-smoke-instance` started on port 8001; HTTP 200 responses verified on `/healthz`, `/readyz`, `/api/ready`, `/api/mcp/status`.
  4. **Level 4 (Public Cloud Deployment):** **NOT PERFORMED** (by design, adhering to non-destructive safety constraints avoiding unauthorized cloud spend or credential leakage).
* **Test Verification:** `tests/test_deployment.py`: 11/11 passed.
* **Status:** **END-TO-END VERIFIED (LOCAL CONTAINER READY)**

---

## 3. Separate Track: Domain Application Capabilities Checklist

The following capabilities represent the product-level test hardening pipeline implemented in TestForge:

| Application Capability | Implementation Location | Test Evidence | Browser Verification Status |
|---|---|---|---|
| **Mode A: Python AST Ingestion** | `testforge/ast_parser.py`, `server.py` | `tests/test_server_routes.py` | **PASS**: Ingestion of `discount.py` and `banking.py` parsed callables and lines. |
| **Mode B: Specification Ingestion** | `testforge/adk_generator.py`, `server.py` | `tests/test_adk_generator.py` | **PASS**: Quick prompt chips populated natural language synthesis textarea. |
| **Mode C: GitHub Direct Import** | `testforge/github_importer.py`, `server.py` | `tests/test_github_importer.py` | **PASS**: Preset repository chips populated URL input with traversal guards. |
| **Blast Radius & Static Call Graph** | `testforge/blast_radius.py`, `server.py` | `tests/test_blast_and_adk.py` | **PASS**: Function selector, risk badge (`🟢 LOW`), ASCII tree, canvas call graph. |
| **Dual-Engine Hardening Loop** | `testforge/orchestrator.py`, `server.py` | `tests/test_crew_critic.py` | **PASS**: Generator synthesis and Critic reflection converged to 100% killed mutants. |
| **Parallel ProcessPool Sandbox** | `testforge/sandbox.py`, `server.py` | `tests/test_sandbox.py` | **PASS**: Parallel worker processes executed mutants with timeout limits. |
| **Deterministic AST Mutation** | `testforge/ast_mutator.py`, `server.py` | `tests/test_ast_mutator.py` | **PASS**: 19 mutants generated with unified diff modal inspection. |
| **SQLite State Checkpointing** | `testforge/state.py`, `testforge/persistence.py` | `tests/test_checkpoints.py` | **PASS**: Snapshot cards, JSON viewer, semantic diff, and safe rollback modal. |
| **Live Wiretap Event Hub** | `testforge/websocket_hub.py`, `frontend/app.js` | `tests/test_websocket_hub.py` | **PASS**: Live WebSocket stream verified; degraded to polling fallback on disconnect. |

---

## 4. Frontend Browser Evidence Reconciliation

The Google Chrome CDP automation performed an exhaustive physical audit of the application:
- **Total Discovered Interactive Controls:** 69
- **Controls Individually Browser-Tested:** 69 (100%)
- **Controls Passing:** 69 (100%)
- **Controls Failing:** 0
- **Controls Blocked / Not Tested:** 0
- **Major Workflows Tested End-to-End:** 12
- **Separation of Evidence Forms:**
  - *Browser Interaction:* All 69 controls were clicked, typed into, toggled, or resized using Chrome CDP commands. Visual DOM changes and modal backdrops were inspected and captured in 21 screenshots.
  - *API Smoke Testing:* 20 FastAPI endpoints were independently probed via HTTP requests before launching browser testing.
  - *Static Source Inspection:* Used to verify non-interactive AST schemas, Pydantic class structures, and absence of prohibited imports.

All 69 controls and their individual actions, expectations, endpoints, and screenshot references are recorded in [FRONTEND_CONTROL_INVENTORY.csv](file:///Users/sourabh/TestForge/qa_artifacts/phase2_master_acceptance_20261023_162200/FRONTEND_CONTROL_INVENTORY.csv).
