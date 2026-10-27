# TESTFORGE — ARCHITECTURAL AUDIT EVIDENCE & SYMBOL INDEX

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:46:00+05:30`  
**Auditor Role:** Senior Software Architect & QA Lead  

---

## 1. Audit Deliverables in this Directory

| Deliverable File | Core Focus |
| :--- | :--- |
| [`EXECUTIVE_REVIEW_READINESS.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/EXECUTIVE_REVIEW_READINESS.md) | High-level review readiness scorecard, key findings, and action summary. |
| [`MUST_REQUIREMENTS_MATRIX.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/MUST_REQUIREMENTS_MATRIX.md) | Exhaustive assessment of all 11 requirements with classes, evidence, and UI mappings. |
| [`BLACKBOARD_DEMONSTRATION_AUDIT.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/BLACKBOARD_DEMONSTRATION_AUDIT.md) | Analysis of shared state creation, agent read/write flows, persistence, and live vs simulated progress. |
| [`MUTATION_ENGINE_CORRECTNESS_AUDIT.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/MUTATION_ENGINE_CORRECTNESS_AUDIT.md) | Audit of score formula, mutant classifications, equivalent mutants, and target status honesty. |
| [`FRONTEND_BACKEND_GAP_ANALYSIS.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/FRONTEND_BACKEND_GAP_ANALYSIS.md) | Analysis of all 28 API contracts, button bindings, loading/error states, and UX gaps. |
| [`PRIORITIZED_IMPLEMENTATION_PLAN.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/PRIORITIZED_IMPLEMENTATION_PLAN.md) | Ranked improvements (P0 to P2) with estimated lines, risks, and test plans awaiting user approval. |
| [`TEACHER_DEMONSTRATION_RUNBOOK.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/TEACHER_DEMONSTRATION_RUNBOOK.md) | 7-step live demonstration script with exact clicks, talking points, and technical disclosures. |
| [`EVIDENCE_INDEX.md`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_readiness_20261027_103800/EVIDENCE_INDEX.md) | This master cross-reference index of symbols, files, and test evidence. |

---

## 2. Source Symbols & Requirement Traceability Index

| # | Course Requirement | Exact Python Classes & Functions | Exact API Endpoints | Primary Frontend UI Elements | Supporting Test Suites |
| :- | :--- | :--- | :--- | :--- | :--- |
| **MUST 1** | **Shared Blackboard** | `testforge.blackboard.Blackboard`<br>`testforge.blackboard.TargetSpace`<br>`testforge.blackboard.SuiteSpace`<br>`testforge.blackboard.MutantSpace`<br>`testforge.blackboard.CriticSpace`<br>`testforge.blackboard.MetricsSpace`<br>`testforge.persistence.SQLiteBlackboardStorage` | `GET /api/checkpoints`<br>`GET /api/checkpoints/{id}`<br>`GET /api/checkpoints/diff`<br>`POST /api/checkpoints/{id}/resume` | Tab: `💾 Checkpoint Timeline & Diff`<br>`#checkpoint-cards-stream`<br>`#view-cp-detail`<br>`#btn-trigger-diff-modal` | `tests/test_blackboard.py`<br>`tests/test_blackboard_persistence.py`<br>`tests/test_checkpoint_diff.py`<br>`tests/test_checkpoint_resumption.py` |
| **MUST 2** | **Genuine MCP Tools** | `testforge.mcp_server.create_filesystem_server`<br>`testforge.mcp_server.create_github_server`<br>`testforge.mcp_client.MCPClientManager` | `GET /api/mcp/status` | Header Button: `🔌 MCP Tools`<br>`#mcp-modal`<br>`#mcp-card-content`<br>`#btn-view-raw-mcp` | `tests/test_mcp.py`<br>`tests/test_orchestration_mcp.py`<br>`tests/test_mcp_status_endpoint.py` |
| **MUST 3** | **Structured Pydantic Outputs** | `testforge.state.TargetMetadata`<br>`testforge.state.MutantRecord`<br>`testforge.state.IterationMetrics`<br>`testforge.crew_critic.CriticDirectiveModel`<br>`testforge.benchmarking.BenchmarkReport` | `GET /api/harden/status/{id}`<br>`GET /api/benchmark/results` | `#mutants-table-body`<br>`#kpi-mut-score`<br>`#kpi-final-status`<br>`#diff-code-display` | `tests/test_mutation_scores.py`<br>`tests/test_benchmarking.py`<br>`tests/test_crew_critic.py` |
| **MUST 4** | **Agentic Pattern Comparison** | `testforge.orchestrator.TestForgeOrchestrator`<br>`testforge.benchmarking.BenchmarkingEngine` | `POST /api/benchmark/run`<br>`GET /api/benchmark/results`<br>`GET /api/benchmark/markdown` | Tab: `⚡ Benchmarks & Ablation`<br>`#benchmark-summary-table`<br>`#bench-rendered-markdown-view` | `tests/test_benchmarking.py`<br>`tests/test_strategy_comparison.py`<br>`tests/test_agentic_pipeline.py` |
| **MUST 5** | **Callbacks & Logging** | `testforge.callbacks.CallbackRegistry`<br>`testforge.callbacks.LifecycleEvent`<br>`testforge.logger.TraceLogger` | `GET /api/telemetry`<br>`GET /api/wiretap`<br>`WS /ws/events` | Tab: `📊 Observability Trace`<br>`#telemetry-table-body`<br>Tab: `🤖 Multi-Agent Wiretap`<br>`#wiretap-cards-container` | `tests/test_callbacks.py`<br>`tests/test_observability.py`<br>`tests/test_websocket_streaming.py` |
| **MUST 6** | **A2A Protocol & Discovery** | `testforge.a2a_protocol.TestForgeA2AExecutor`<br>`testforge.a2a_protocol.TestForgeAgentCard`<br>`testforge.a2a.A2ABroker` | `GET /.well-known/agent-card.json`<br>`GET /.well-known/agent.json`<br>`POST /a2a/tasks` | Header Button: `🤖 A2A Agent Card`<br>`#a2a-modal`<br>`#a2a-card-content`<br>`#btn-view-raw-a2a` | `tests/test_a2a_protocol.py`<br>`tests/test_a2a.py`<br>`tests/test_a2a_card_ui_and_endpoint.py` |
| **MUST 7** | **CrewAI & Google ADK** | `testforge.adk_generator.GoogleADKTestGenerator`<br>`testforge.crew_critic.CrewAICriticAgent` | `GET /api/harden/status/{id}` | Tab: `🤖 Multi-Agent Wiretap`<br>`#kpi-active-provider`<br>`#engine-mode-select` | `tests/test_adk_generator.py`<br>`tests/test_crew_critic.py`<br>`tests/test_blast_and_adk.py` |
| **MUST 8** | **Security Guardrails** | `testforge.security.SecurityGuardrail`<br>`testforge.security.SecurityPolicy`<br>`testforge.security.redact_sensitive_data`<br>`testforge.sandbox.SubprocessSandbox` | Pre-execution AST check<br>SSRF validator | `#mode-a-error-alert`<br>`#mode-c-error-alert`<br>Redacted log spans | `tests/test_security.py`<br>`tests/test_adversarial_failure_injection.py`<br>`tests/test_mode_c_ingestion.py` |
| **MUST 9** | **Observability & Provenance** | `testforge.logger.TraceLogger.get_provenance_chain`<br>`testforge.logger.TraceRecord` | `GET /api/telemetry`<br>`GET /api/wiretap` | `#diff-code-display` (Survivor Diagnosis & Sandbox Verification Box)<br>`#telemetry-kpi-events` | `tests/test_observability.py`<br>`tests/test_agentic_pipeline.py` |
| **MUST 10**| **Multi-Run Benchmarks & Cost** | `testforge.benchmarking.BenchmarkingEngine`<br>`testforge.benchmarking.PRICING_TABLE_PER_MILLION`<br>`testforge.benchmarking.MetricBreakdown` | `GET /api/benchmark/results`<br>`GET /api/benchmark/markdown` | Tab: `⚡ Benchmarks & Ablation`<br>`#benchmark-models-table`<br>`#btn-bench-md-rendered` | `tests/test_benchmarking.py`<br>`tests/test_fast_benchmarking.py`<br>`tests/test_messaging_benchmark.py` |
| **MUST 11**| **Cloud Deployment Readiness** | `Dockerfile`<br>`docker-compose.yml`<br>`server.py:health_check`<br>`server.py:readiness_check` | `GET /healthz`<br>`GET /readyz`<br>`GET /api/ready` | Footer connection badges<br>`#status-ping` | `tests/test_deployment.py` |

---

## 3. Persistent Database & Historical Benchmark Records

1. **SQLite Checkpoint Store:**
   - Path: `qa_artifacts/testforge_checkpoints.db`
   - Real persistent records for jobs: `5f996812` (`discount.py`), `012bc18d` (`banking.py`), `39a9cd38` (`inventory_pricing.py`), `f5bc10ce` (`state_machine.py`), `90e26c48` (`rate_limiter.py`).
2. **Empirical Benchmark Datasets:**
   - Path: `benchmark_results.json` & `benchmark_results.md`
   - Content: Multi-condition statistical comparison of Baseline, Zero-Shot, and Agentic Reflection with token counts and USD costs.
3. **Structured JSONL Event Trace:**
   - Path: `testforge_trace.jsonl`
   - Content: Thousands of typed `LifecycleEvent` objects with `correlation_id` and secret masking.
