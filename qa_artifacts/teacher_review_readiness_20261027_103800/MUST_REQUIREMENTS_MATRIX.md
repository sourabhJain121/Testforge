# TESTFORGE — 11 MANDATORY REQUIREMENTS EVIDENCE & VERIFICATION MATRIX

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:40:00+05:30`  
**Evaluation Standard:** CSE3101 Autonomous Agentic Systems Rigorous Rubric  

---

## Master Classification Summary

| # | Mandatory Course Requirement | Verified Status | Architecture & Source Files | Automated Test Evidence | Frontend UI Component |
| :- | :--- | :---: | :--- | :--- | :--- |
| **MUST 1** | **Blackboard / Shared State** | **VERIFIED** | `testforge/blackboard.py`<br>`testforge/persistence.py`<br>`testforge/orchestrator.py` | `tests/test_blackboard.py` (18 passed)<br>`tests/test_blackboard_persistence.py` (22 passed) | Tab: `💾 Checkpoint Timeline & Diff` (`#tab-checkpoints`) |
| **MUST 2** | **$\ge 2$ Genuine MCP Tools** | **VERIFIED** | `testforge/mcp_server.py`<br>`testforge/mcp_client.py`<br>`server.py:263` | `tests/test_mcp.py` (22 passed)<br>`tests/test_orchestration_mcp.py` (19 passed) | Header Modal: `🔌 MCP Tools` (`#mcp-modal`), `/api/mcp/status` |
| **MUST 3** | **Structured Pydantic Outputs** | **VERIFIED** | `testforge/state.py`<br>`testforge/crew_critic.py`<br>`testforge/benchmarking.py` | `tests/test_mutation_scores.py` (9 passed)<br>`tests/test_benchmarking.py` (6 passed) | Tab: `🔥 Hardening Lab`, `📊 Observability Trace`, Checkpoint JSON |
| **MUST 4** | **Agentic Pattern Comparison** | **VERIFIED** | `testforge/benchmarking.py`<br>`run_benchmark.py`<br>`testforge/orchestrator.py` | `tests/test_benchmarking.py` (6 passed)<br>`tests/test_strategy_comparison.py` (7 passed) | Tab: `⚡ Benchmarks & Ablation` (`#tab-benchmark`) |
| **MUST 5** | **Callbacks & Logging** | **VERIFIED** | `testforge/callbacks.py`<br>`testforge/logger.py`<br>`server.py` | `tests/test_callbacks.py` (12 passed)<br>`tests/test_observability.py` (7 passed) | Tab: `📊 Observability Trace` (`#tab-telemetry`) |
| **MUST 6** | **A2A Discovery & Protocol** | **VERIFIED** | `testforge/a2a_protocol.py`<br>`testforge/a2a.py`<br>`server.py:340` | `tests/test_a2a_protocol.py` (15 passed)<br>`tests/test_a2a.py` (15 passed) | Header Modal: `🤖 A2A Agent Card` (`#a2a-modal`), `/.well-known/agent-card.json` |
| **MUST 7** | **CrewAI & Google ADK** | **VERIFIED** | `testforge/adk_generator.py`<br>`testforge/crew_critic.py`<br>`testforge/orchestrator.py` | `tests/test_adk_generator.py` (14 passed)<br>`tests/test_crew_critic.py` (9 passed) | Tab: `🤖 Multi-Agent Wiretap` (`#tab-wiretap`), Active Provider Badges |
| **MUST 8** | **Security Guardrails** | **VERIFIED** | `testforge/security.py`<br>`testforge/sandbox.py`<br>`testforge/ingestion.py` | `tests/test_security.py` (30 passed)<br>`tests/test_adversarial_failure_injection.py` (18 passed) | Pre-execution AST Error Banners, Redacted Logs |
| **MUST 9** | **Observability & Provenance** | **VERIFIED** | `testforge/logger.py`<br>`server.py:1228` | `tests/test_observability.py` (7 passed)<br>`tests/test_agentic_pipeline.py` (5 passed) | Tab: `📊 Observability Trace`, Surviving Mutant Sandbox Output Box |
| **MUST 10**| **Multi-Run Benchmarking & Cost**| **VERIFIED**| `testforge/benchmarking.py`<br>`benchmark_results.json` | `tests/test_benchmarking.py` (6 passed)<br>`tests/test_fast_benchmarking.py` (4 passed) | Tab: `⚡ Benchmarks & Ablation` (JSON/MD raw endpoints) |
| **MUST 11**| **Cloud Deployment Readiness** | **VERIFIED** | `Dockerfile`<br>`docker-compose.yml`<br>`server.py:178` | `tests/test_deployment.py` (11 passed) | Liveness `/healthz`, Readiness `/readyz`, Container Config |

---

## Detailed Requirement Audits

### MUST 1 — Blackboard / Shared State Architecture
- **Implementation:** `testforge/blackboard.py` (`Blackboard`), `testforge/persistence.py` (`SQLiteBlackboardStorage`), `testforge/orchestrator.py`.
- **Functionality:** Thread-safe (`threading.RLock()`), revision-controlled, 5-partition state coordinator (`TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, `MetricsSpace`). Writes immutable point-in-time snapshots to SQLite database `testforge_checkpoints.db` at orchestration boundaries.
- **Evidence:** `tests/test_blackboard.py` (18 passed), `tests/test_blackboard_persistence.py` (22 passed), `tests/test_checkpoint_diff.py` (11 passed).
- **Frontend Exposure:** Tab `💾 Checkpoint Timeline & Diff` (`#tab-checkpoints`). Displays snapshot stream, renders all 5 partition cards on inspection, and provides a deterministic diff between snapshots.
- **Demonstrability:** Teacher can click `💾 Checkpoint Timeline & Diff`, pick any snapshot, inspect all 5 partitions, and diff `BASELINE_VALIDATED` vs `FINALIZED`.
- **Smallest Improvement:** Add a compact 5-space status strip in the primary `🔥 Hardening Lab` tab to show live partition writes during execution.
- **Status:** **VERIFIED**

---

### MUST 2 — At Least Two Genuine MCP Tool Integrations
- **Implementation:** `testforge/mcp_server.py` (`create_filesystem_server`, `create_github_server`), `testforge/mcp_client.py` (`MCPClientManager`), `server.py:263` (`/api/mcp/status`).
- **Functionality:** Uses official `FastMCP` (Model Context Protocol). Exposes two distinct FastMCP servers over stdio JSON-RPC:
  1. Filesystem Server: `read_text_file`, `list_directory`, `get_file_info` with path confinement and credential blocking.
  2. GitHub Server: `get_repository_info`, `get_file_contents`, `search_repositories` with rate-limit handling.
  `MCPClientManager` validates arguments against Pydantic schemas, handles timeouts, and syncs tool metadata to Blackboard.
- **Evidence:** `tests/test_mcp.py` (22 passed), `tests/test_orchestration_mcp.py` (19 passed). `curl -s http://127.0.0.1:8000/api/mcp/status` returns operational status with 4 registered tools.
- **Frontend Exposure:** Navbar button `🔌 MCP Tools` (`#btn-mcp-status`) opens `#mcp-modal` displaying servers, tools, schemas, and links to raw endpoint.
- **Demonstrability:** Teacher can click `🔌 MCP Tools` in navbar, inspect tools and schemas, or click "View Raw JSON".
- **Smallest Improvement:** Add an interactive "Run FastMCP Tool" test button inside `#mcp-modal` to execute a safe read on demand without terminal.
- **Status:** **VERIFIED**

---

### MUST 3 — Structured Pydantic Outputs
- **Implementation:** `testforge/state.py`, `testforge/crew_critic.py`, `testforge/adk_generator.py`, `testforge/benchmarking.py`.
- **Functionality:** All inter-agent payloads, LLM responses, Blackboard spaces, and API schemas use Pydantic v2 `BaseModel` classes with strict validation. Critic outputs are parsed with `.model_validate_json()` with markdown stripping and fallback guards.
- **Evidence:** `tests/test_mutation_scores.py` (9 passed), `tests/test_benchmarking.py` (6 passed).
- **Frontend Exposure:** Rendered across all tables, JSON exports, and cards.
- **Demonstrability:** Teacher can inspect structured outputs in the Checkpoint JSON view or API endpoints.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 4 — Agentic Pattern Comparison (Evaluator-Optimizer / Reflection)
- **Implementation:** `testforge/orchestrator.py` (reflection loop), `testforge/benchmarking.py` (`BenchmarkingEngine`), `run_benchmark.py`.
- **Functionality:** Implements multi-agent reflection: Google ADK synthesizes tests -> clean code validation -> AST Mutator injects faults -> parallel sandbox evaluates -> CrewAI Critic diagnoses surviving diffs -> ADK synthesizes hardened assertions. Formal 3-condition ablation compares Baseline (handwritten) vs Zero-Shot (single-pass LLM) vs Agentic Reflection across latency, score, coverage, tokens, and cost.
- **Evidence:** `tests/test_benchmarking.py` (6 passed), `tests/test_strategy_comparison.py` (7 passed), `benchmark_results.json`, `benchmark_results.md`.
- **Frontend Exposure:** Tab `⚡ Benchmarks & Ablation` (`#tab-benchmark`) displays comparative summary table, model pricing, and Markdown report.
- **Demonstrability:** Teacher opens `⚡ Benchmarks & Ablation` tab to view comparison or triggers a new run.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 5 — Callback-Based Task Monitoring & Logging
- **Implementation:** `testforge/callbacks.py` (`CallbackRegistry`), `testforge/logger.py` (`TraceLogger`), `server.py` (`/api/telemetry`, `/api/wiretap`, `/ws/events`).
- **Functionality:** Publisher-subscriber architecture emitting 11 typed lifecycle events (`OPERATION_START/COMPLETE`, `AGENT_START/COMPLETE`, `TOOL_CALL`, `STATE_UPDATE`, `ERROR`, etc.). Isolated subscriber exceptions prevent crashes. Synchronous JSONL logging to `testforge_trace.jsonl` with credential scrubbing. Real-time WebSocket streaming.
- **Evidence:** `tests/test_callbacks.py` (12 passed), `tests/test_observability.py` (7 passed), `tests/test_websocket_streaming.py` (6 passed).
- **Frontend Exposure:** Tab `📊 Observability Trace` (searchable event log table) and Tab `🤖 Multi-Agent Wiretap` (agent handoff cards).
- **Demonstrability:** Teacher opens Telemetry or Wiretap tab and views live/persisted events.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 6 — Official A2A Discovery & Protocol
- **Implementation:** `testforge/a2a_protocol.py` (`TestForgeA2AExecutor`), `testforge/a2a.py`, `server.py:340` (`/.well-known/agent-card.json`, `/a2a/tasks`).
- **Functionality:** Built using official `a2a-sdk==0.3.26` (Protocol v0.3.0). Publishes AgentCard discovery at standard `/.well-known/agent-card.json`. Wire protocol dispatches JSON-RPC 2.0 tasks to ADK generator or CrewAI critic with lifecycle states (`submitted` -> `working` -> `completed`/`failed`).
- **Evidence:** `tests/test_a2a_protocol.py` (15 passed), `tests/test_a2a.py` (15 passed), `tests/test_a2a_card_ui_and_endpoint.py` (4 passed). `curl -s http://127.0.0.1:8000/.well-known/agent-card.json` returns valid schema.
- **Frontend Exposure:** Navbar button `🤖 A2A Agent Card` (`#btn-a2a-card`) opens `#a2a-modal` showing capabilities, version, endpoints, and raw JSON link.
- **Demonstrability:** Teacher clicks `🤖 A2A Agent Card` or curls `/.well-known/agent-card.json`.
- **Smallest Improvement:** Add an interactive "Send Test A2A Ping" button inside `#a2a-modal` to demonstrate live protocol execution without terminal.
- **Status:** **VERIFIED**

---

### MUST 7 — CrewAI & Google ADK Integration (Without 3rd Framework)
- **Implementation:** `testforge/adk_generator.py` (Google ADK `LlmAgent`), `testforge/crew_critic.py` (CrewAI `Agent`, `Task`, `Crew`), `testforge/orchestrator.py`.
- **Functionality:** Both frameworks actively participate: Google ADK synthesizes and hardens tests; CrewAI inspects mutant diffs and produces adversarial directives. No third framework (LangChain, AutoGen, LangGraph) exists in the repo.
- **Evidence:** `tests/test_adk_generator.py` (14 passed), `tests/test_crew_critic.py` (9 passed), `tests/test_blast_and_adk.py` (5 passed).
- **Frontend Exposure:** Tab `🤖 Multi-Agent Wiretap` displays explicit handoff cards between ADK Generator and CrewAI Critic. Provider badges display active engine.
- **Demonstrability:** Teacher opens `🤖 Multi-Agent Wiretap` to view handoff cards and payloads.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 8 — Security Guardrails & Prompt Variants
- **Implementation:** `testforge/security.py` (`SecurityGuardrail`, `SecurityPolicy`), `testforge/sandbox.py` (`SubprocessSandbox`), `testforge/ingestion.py`.
- **Functionality:** Pre-execution AST filter blocks dangerous calls (`eval`, `exec`, `os.system`, `subprocess`, `socket`). Prompt injection scanner blocks role overrides and secret extraction. Toxicity scanner blocks abuse while allowing domain terms ("kill mutant"). SSRF validator blocks loopback, private IPs, and metadata endpoints. Regex redacts secrets in logs.
- **Evidence:** `tests/test_security.py` (30 passed), `tests/test_adversarial_failure_injection.py` (18 passed), `tests/test_mode_c_ingestion.py` (10 passed).
- **Frontend Exposure:** Mode A/B/C display security error banners when dangerous code or URLs are entered. All logs redact secrets.
- **Demonstrability:** Teacher submits dangerous snippet or runs security test suite.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 9 — Observability & Provenance
- **Implementation:** `testforge/logger.py` (`TraceLogger`, `get_provenance_chain`), `server.py:1228`.
- **Functionality:** Every mutant can be queried for its complete lifecycle provenance: AST mutation -> sandbox evaluation -> critic directive -> hardened test -> final kill status. Top-level `workflow_id` and `correlation_id` link all events.
- **Evidence:** `tests/test_observability.py` (7 passed), `tests/test_agentic_pipeline.py` (5 passed).
- **Frontend Exposure:** Tab `📊 Observability Trace` and the Surviving Mutant Diagnosis pane (which shows sandbox execution time, AST semantics, and raw pytest output).
- **Demonstrability:** Teacher selects any mutant in the mutants table to inspect the Diagnosis and real sandbox proof.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 10 — Multi-Run Benchmarking & Cost
- **Implementation:** `testforge/benchmarking.py` (`BenchmarkingEngine`, `PRICING_TABLE_PER_MILLION`), `server.py:1339`, `run_benchmark.py`.
- **Functionality:** Runs $N \ge 1$ repetitions across 5 standard sample files. Computes mean and standard deviation for latency, mutation score, and coverage. Categorizes metrics into measured, calculated, and estimated financial cost in USD using published Google Gemini rates. Exports to JSON and Markdown.
- **Evidence:** `tests/test_benchmarking.py` (6 passed), `tests/test_fast_benchmarking.py` (4 passed), `benchmark_results.json`, `benchmark_results.md`.
- **Frontend Exposure:** Tab `⚡ Benchmarks & Ablation` displays summary table, model pricing breakdown, and Markdown preview.
- **Demonstrability:** Teacher opens `⚡ Benchmarks & Ablation` tab and inspects tables and raw endpoints.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**

---

### MUST 11 — Cloud Deployment Readiness
- **Implementation:** `Dockerfile`, `docker-compose.yml`, `server.py:178` (`/healthz`, `/readyz`), `docs/DEPLOYMENT_GUIDE.md`.
- **Functionality:** Cloud liveness probe `GET /healthz` (uptime, server status) and deep readiness probe `GET /readyz` (CPU, memory headroom, disk, Python runtime). Multi-stage production Docker containerization.
- **Evidence:** `tests/test_deployment.py` (11 passed). `curl -s http://127.0.0.1:8000/healthz` returns `{"status":"ok"}`.
- **Frontend Exposure:** Server connection badges in footer and navbar. Direct endpoints accessible via browser.
- **Demonstrability:** Teacher curls `/healthz` and `/readyz` or inspects `Dockerfile`.
- **Smallest Improvement:** None required.
- **Status:** **VERIFIED**
