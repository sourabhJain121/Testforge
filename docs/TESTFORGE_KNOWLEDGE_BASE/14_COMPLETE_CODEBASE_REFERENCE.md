# TestForge — Complete Codebase Architecture & File Reference

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Repository Working Directory:** `/Users/sourabh/TestForge`  

---

## 1. Complete `testforge/` Module Map (All 32 Modules)

| # | File Path | Main Classes / Functions | Primary Responsibility | Tested By |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `testforge/__init__.py` | Package root metadata | Initializes package namespace and version info. | `tests/test_deployment.py` |
| **2** | `testforge/a2a.py` | `A2APerformative`, `A2AMessage`, `A2ABroker`, `AgentHandlerRegistration` | FIPA-ACL message envelope validation, broker routing, and inter-agent communication. | `tests/test_a2a.py` |
| **3** | `testforge/a2a_protocol.py` | `TestForgeA2AExecutor`, `TestForgeA2AClient` | Implements official A2A protocol gateway, card resolution, and external agent bridge. | `tests/test_a2a_protocol.py` |
| **4** | `testforge/accel.py` | `HardwareProfile`, `hw_profile` | Inspects host CPU/RAM/Metal GPU capabilities for optimal parallel worker scaling. | `tests/test_benchmarking.py` |
| **5** | `testforge/adk_engine.py` | `ADKExecutionEngine` | Low-level execution runner for Google ADK workflows. | `tests/test_adk_generator.py` |
| **6** | `testforge/adk_generator.py`| `GoogleADKTestGenerator`, `ADKModelBridge`, `GeneratorCriticWorkflow` | Google ADK `LlmAgent` implementation of the generator agent. | `tests/test_adk_generator.py` |
| **7** | `testforge/agents.py` | `TestGeneratorAgent`, `AdversarialCriticAgent`, `CodeSanitizer` | Core native generator and critic agents, AST sanitization, and reflection refinement. | `tests/test_agents.py` |
| **8** | `testforge/benchmark_messaging.py` | `MessagingBenchmarkRunner` | Evaluates inter-agent message throughput, broker latency, and queue scaling. | `tests/test_messaging_benchmark.py` |
| **9** | `testforge/benchmarking.py`| `BenchmarkRunner`, `BenchmarkReport` | Core ablation study runner executing empirical performance matrices. | `tests/test_benchmarking.py` |
| **10** | `testforge/blackboard.py` | `Blackboard`, `TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, `MetricsSpace` | Central, thread-safe, typed shared state repository with event notifications and snapshots. | `tests/test_blackboard.py` |
| **11** | `testforge/blast_analyzer.py`| `BlastRadiusAnalyzer` | Analyzes dependency blast radius of target modifications using AST call graphs. | `tests/test_blast_and_adk.py` |
| **12** | `testforge/callbacks.py` | `BaseCallbackHandler`, `CompositeCallbackHandler`, `WiretapCallbackHandler` | Lifecycle event hooks emitting typed payloads to logger, wiretap, and websockets. | `tests/test_callbacks.py` |
| **13** | `testforge/classifier.py` | `TestClassifier` | Categorizes tests into unit, integration, boundary, and regression types. | `tests/test_classifier.py` |
| **14** | `testforge/cli.py` | `main` | Command-line interface for running hardening jobs directly from terminal. | `tests/test_deployment.py` |
| **15** | `testforge/crew_critic.py` | `CrewAICriticAgent`, `CrewAILLMBridge` | CrewAI `Agent` implementation of the adversarial critic. | `tests/test_crew_critic.py` |
| **16** | `testforge/diff_inspector.py`| `DiffInspector`, `compute_ast_diff` | Computes syntax-highlighted semantic unified diffs between test suites. | `tests/test_checkpoint_diff.py` |
| **17** | `testforge/equivalence.py` | `EquivalentMutantAnalyzer`, `DeadCodeVisitor` | Conservative equivalence analyzer proving dead-code and self-canceling mutants. | `tests/test_equivalent_mutants.py` |
| **18** | `testforge/git_diff.py` | `GitDiffInspector` | Inspects git working-tree diffs to identify modified lines for targeted mutation. | `tests/test_mode_c_ingestion.py` |
| **19** | `testforge/github_service.py`| `GitHubService` | Ingests remote repositories with rate-limiting, authentication, and payload bounding. | `tests/test_mode_c_ingestion.py` |
| **20** | `testforge/guidance.py` | `derive_semantic_guidance` | Generates semantic boundary hints from surviving mutant diffs. | `tests/test_mutation_guided_repair.py` |
| **21** | `testforge/ingestion.py` | `TargetManagerAgent`, `IngestionMode` | Manages Mode A, B, and C source ingestion, threat scanning, and TargetSpace creation. | `tests/test_ingestion_and_llm.py` |
| **22** | `testforge/intelligent_generator.py` | `IntelligentASTSynthesizer`, `ASTCallableAnalyzer`, `ReferenceExecutor` | Intelligent AST test synthesis, boundary extraction, and reference execution. | `tests/test_ast_scope_extraction.py` |
| **23** | `testforge/llm_client.py` | `HybridLLMClient`, `is_ollama_running` | 4-tier inference client (Gemini $\rightarrow$ OpenRouter $\rightarrow$ Ollama $\rightarrow$ AST Synthesizer). | `tests/test_token_observability_audit.py` |
| **24** | `testforge/logger.py` | `TraceLogger`, `resolve_dynamic_execution_engine` | Appends events to `testforge_trace.jsonl`, calculates actual vs estimated tokens, resolves dynamic KPI. | `tests/test_dynamic_model_identification.py` |
| **25** | `testforge/mcp_client.py` | `create_filesystem_client`, `create_github_client` | Client transport invoking FastMCP tools over stdio/JSON-RPC. | `tests/test_mcp.py` |
| **26** | `testforge/mcp_server.py` | `create_filesystem_server`, `create_github_server` | Implements native FastMCP Filesystem and GitHub servers with security path guards. | `tests/test_mcp_network_security.py` |
| **27** | `testforge/mutator.py` | `ASTMutator`, `MutationTransformer` | AST-level mutation operator generator producing syntactically valid mutants. | `tests/test_mutator.py` |
| **28** | `testforge/network_security.py` | `validate_url_hostname`, `bounded_read` | SSRF prevention, private IP blocking, and payload size restriction for remote fetching. | `tests/test_network_security.py` |
| **29** | `testforge/orchestrator.py` | `TestForgeOrchestrator`, `TaskLifecycleFSM` | Central supervisor orchestrating multi-agent reflection loops and FSM transitions. | `tests/test_task_lifecycle.py` |
| **30** | `testforge/performance_evaluator.py` | `PerformanceEvaluator` | End-to-end benchmarking harness evaluating prompt strategies and personas. | `tests/test_performance_evaluation.py` |
| **31** | `testforge/persistence.py` | `SQLiteBlackboardStorage`, `CheckpointMetadata` | SQLite repository managing 1,310 durable checkpoints with WAL journaling. | `tests/test_blackboard_persistence.py` |
| **32** | `testforge/prompt_guard.py` | `scan_for_injection_attempts` | Detects adversarial prompt injection attempts in user-supplied source or docstrings. | `tests/test_prompt_injection_defense.py` |
| **33** | `testforge/sandbox.py` | `NativeSandbox`, `ExecutionResult` | Executes Pytest and mutants in isolated native subprocesses with timeouts. | `tests/test_sandbox.py` |
| **34** | `testforge/security.py` | `redact_sensitive_data`, `is_safe_code` | Secrets redaction (API keys, passwords) and static security validation. | `tests/test_security.py` |
| **35** | `testforge/security_evaluation_engine.py` | `SecurityEvaluationEngine` | Deterministic security harness evaluating 10 attack scenarios across 120 trials. | `tests/test_security_variations.py` |
| **36** | `testforge/security_prompts.py` | `build_security_prompt` | Prompt builders for Zero-Shot, Few-Shot, and ReAct across 4 developer personas. | `tests/test_security_variations.py` |
| **37** | `testforge/state.py` | `MutantRecord`, `HardeningJobState` | Core Pydantic data models for mutant tracking, test execution, and job state. | `tests/test_state.py` |
| **38** | `testforge/websocket_hub.py`| `WebSocketHub`, `global_websocket_hub` | Manages real-time WebSocket client connections for live wiretap event streaming. | `tests/test_websocket_streaming.py` |

---

## 2. Core Root and Web Modules

- **`server.py`:** FastAPI application server hosting REST endpoints, SSE stream (`/api/wiretap`), no-cache static files, and background task management.
- **`test_hardened.py`:** Authoritative behavioral test suite achieving 89.47% discount and 68.22% logistics raw mutation kill rates.
- **`frontend/index.html`:** Single-page dashboard interface featuring Workbench, Wiretap, Checkpoints, Telemetry, and Benchmarking tabs.
- **`frontend/app.js`:** Pure JavaScript application controller driving UI interactivity, SSE event handling, dynamic KPI rendering, and modal diffs.
- **`frontend/styles.css`:** Modern cyber-dark glassmorphism styling system.

