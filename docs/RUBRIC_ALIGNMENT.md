# TestForge Phase-3 Rubric Alignment Matrix

> **Course**: Autonomous Agentic AI (16 Weeks, Phase-3 Evaluation)  
> **Authors**: Sourabh & Shreshth  
> **Mode**: INTEGRITY FIRST, THEN EVIDENCE, THEN FEATURES, THEN POLISH  
> **Branch**: `feat/final-evidence`  

---

## 1. Core Handout Criteria (Features F1 through F9)

| Rubric Feature | Architectural Requirement | Source Code Implementation | Automated Pytest Suite | Empirical Evidence File |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | 8-Partition Atomic Blackboard | [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py) (`Blackboard`, 8 spaces, `RLock`, SQLite WAL) | [`tests/test_blackboard.py`](file:///Users/sourabh/TestForge/tests/test_blackboard.py) (18 passed), [`tests/test_blackboard_8space_expansion.py`](file:///Users/sourabh/TestForge/tests/test_blackboard_8space_expansion.py) (12 passed) | `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json` |
| **F2** | Dual Agentic Frameworks (Google ADK + CrewAI) | [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py), [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py), [`testforge/supervisor_agent.py`](file:///Users/sourabh/TestForge/testforge/supervisor_agent.py) | [`tests/test_adk_production_path.py`](file:///Users/sourabh/TestForge/tests/test_adk_production_path.py) (3 passed), [`tests/test_crew_critic.py`](file:///Users/sourabh/TestForge/tests/test_crew_critic.py) (9 passed) | `docs/ADK_EVAL_REPORT.md` |
| **F3** | Agent2Agent (A2A v0.3.0) Wire Protocol | [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py), [`testforge/a2a_protocol.py`](file:///Users/sourabh/TestForge/testforge/a2a_protocol.py), [`testforge/a2a_distributed.py`](file:///Users/sourabh/TestForge/testforge/a2a_distributed.py) | [`tests/test_a2a_protocol.py`](file:///Users/sourabh/TestForge/tests/test_a2a_protocol.py) (15 passed), [`tests/test_distributed_cross_process_a2a.py`](file:///Users/sourabh/TestForge/tests/test_distributed_cross_process_a2a.py) (1 passed) | `docs/A2A_PROTOCOL_SPECIFICATION.md` |
| **F4** | ADK Deliberation, Callbacks & Output Guardrails | [`testforge/adk_callbacks.py`](file:///Users/sourabh/TestForge/testforge/adk_callbacks.py), [`testforge/security.py`](file:///Users/sourabh/TestForge/testforge/security.py) | [`tests/test_adk_callbacks.py`](file:///Users/sourabh/TestForge/tests/test_adk_callbacks.py) (12 passed), [`tests/test_guardrails_approval.py`](file:///Users/sourabh/TestForge/tests/test_guardrails_approval.py) (6 passed) | `qa_artifacts/SECURITY_EVALUATION_REPORT.json` |
| **F5** | FastMCP Client & Stdio Server | [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py), [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py), [`testforge/adk_mcp_adapter.py`](file:///Users/sourabh/TestForge/testforge/adk_mcp_adapter.py) | [`tests/test_testforge_mcp_server.py`](file:///Users/sourabh/TestForge/tests/test_testforge_mcp_server.py) (2 passed), [`tests/test_adk_mcp_integration.py`](file:///Users/sourabh/TestForge/tests/test_adk_mcp_integration.py) (3 passed) | `docs/MCP_ADK_INTEGRATION.md` |
| **F6** | OpenTelemetry W3C Tracing & Telemetry | [`testforge/observability.py`](file:///Users/sourabh/TestForge/testforge/observability.py) (`TestForgeOtelTracer`), [`testforge/logger.py`](file:///Users/sourabh/TestForge/testforge/logger.py) | [`tests/test_observability.py`](file:///Users/sourabh/TestForge/tests/test_observability.py) (4 passed) | `qa_artifacts/OPENTELEMETRY_TRACES.json` |
| **F7** | Persistent Checkpoint Timeline & Semantic Diff | [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py), [`testforge/checkpoint_diff.py`](file:///Users/sourabh/TestForge/testforge/checkpoint_diff.py) | [`tests/test_checkpoint_diff.py`](file:///Users/sourabh/TestForge/tests/test_checkpoint_diff.py) (11 passed), [`tests/test_checkpoint_resumption.py`](file:///Users/sourabh/TestForge/tests/test_checkpoint_resumption.py) (17 passed) | `docs/TESTFORGE_CHECKPOINT_TIMELINE_AND_DIFF_INSPECTOR.md` |
| **F8** | Subprocess & Live Docker Sandbox Backend | [`testforge/sandbox.py`](file:///Users/sourabh/TestForge/testforge/sandbox.py), [`testforge/docker_sandbox.py`](file:///Users/sourabh/TestForge/testforge/docker_sandbox.py) | [`tests/test_sandbox_backend.py`](file:///Users/sourabh/TestForge/tests/test_sandbox_backend.py) (7 passed) | `qa_artifacts/DOCKER_VERIFICATION_LOG.md` |
| **F9** | Standalone CLI, Containerization & CI/CD Probes | [`testforge/cli.py`](file:///Users/sourabh/TestForge/testforge/cli.py), [`Dockerfile`](file:///Users/sourabh/TestForge/Dockerfile), [`server.py`](file:///Users/sourabh/TestForge/server.py) (`/healthz`, `/readyz`) | [`tests/test_production_packaging_and_cli.py`](file:///Users/sourabh/TestForge/tests/test_production_packaging_and_cli.py) (7 passed), [`tests/test_deployment.py`](file:///Users/sourabh/TestForge/tests/test_deployment.py) (11 passed) | `docs/DEPLOYMENT_GUIDE.md` |

---

## 2. Advanced Phase-3 Criteria (Beyond Handout C11 through C15)

### Criterion C11: Zero-Egress Privacy Mode & PII Scrubbing
- **Implementation**: [`testforge/privacy_mode.py`](file:///Users/sourabh/TestForge/testforge/privacy_mode.py) (`PrivacyModeManager`, `ZeroEgressSocketInterceptor`).
- **Capabilities**:
  - Dynamically monkeypatches low-level OS `socket.socket.connect` to block 100% of outbound external TCP connections while permitting local loopback IPC (`127.0.0.1:11434` for Ollama).
  - Pre-inference regex sanitization scrubs 7 categories of sensitive secrets and PII (Gemini keys, OpenRouter keys, GitHub tokens, passwords, emails, SSNs, phone numbers).
  - Automated cloud LLM rerouting to local `qwen2.5-coder:7b`.
- **Verification Tests**: [`tests/test_privacy_mode.py`](file:///Users/sourabh/TestForge/tests/test_privacy_mode.py) (6 passed).
- **Evidence Artifacts**: [`qa_artifacts/PRIVACY_MODE_EVIDENCE.json`](file:///Users/sourabh/TestForge/qa_artifacts/PRIVACY_MODE_EVIDENCE.json), [`docs/PRIVACY_MODE_EVIDENCE.md`](file:///Users/sourabh/TestForge/docs/PRIVACY_MODE_EVIDENCE.md).

---

### Criterion C12: Multimodal Architecture & Vision Inputs
- **Implementation**: [`testforge/multimodal_fsm.py`](file:///Users/sourabh/TestForge/testforge/multimodal_fsm.py) (`MultimodalFSMDeriver`).
- **Capabilities**:
  - Synthesizes robust unit test suites directly from visual architectural state machine diagrams (`tests/fixtures/fsm_diagram.png`).
  - Supports Gemini Vision (`gemini-3.6-flash`) with deterministic offline topology fallback.
  - Generates 7 comprehensive test suites covering 10 states, 12 transitions, 3 terminal states, and RBAC / $5000 guards.
  - Measured **74.5% raw mutation kill rate (79/106 mutants)** out-of-the-box from visual diagram inputs alone.
- **Verification Tests**: [`tests/test_multimodal_fsm.py`](file:///Users/sourabh/TestForge/tests/test_multimodal_fsm.py) (5 passed).
- **Evidence Artifacts**: [`docs/MULTIMODAL_FSM_DERIVATION.md`](file:///Users/sourabh/TestForge/docs/MULTIMODAL_FSM_DERIVATION.md), [`tests/fixtures/fsm_diagram.png`](file:///Users/sourabh/TestForge/tests/fixtures/fsm_diagram.png).

---

### Criterion C13: Test Suite Minimization & Kill Matrix Compression
- **Implementation**: [`testforge/minimizer.py`](file:///Users/sourabh/TestForge/testforge/minimizer.py) (`TestSuiteMinimizer`).
- **Capabilities**:
  - Formulates test redundancy elimination as the NP-hard minimum set cover problem on the 2D Boolean Kill Matrix $M \in \{0, 1\}^{|T| \times |K|}$.
  - Solves using greedy set cover approximation to find the minimal subset of tests covering all killable mutants.
  - Across 4 canonical benchmark modules, compressed test suite from 134 tests down to 28 tests (**79.1% macro reduction**) with **strictly 100.0% mutation score retention** (0 dropped kills).
- **Verification Tests**: [`tests/test_suite_minimizer.py`](file:///Users/sourabh/TestForge/tests/test_suite_minimizer.py) (4 passed).
- **Evidence Artifacts**: [`qa_artifacts/SUITE_MINIMIZATION_RESULTS.json`](file:///Users/sourabh/TestForge/qa_artifacts/SUITE_MINIMIZATION_RESULTS.json), [`docs/SUITE_MINIMIZATION_REPORT.md`](file:///Users/sourabh/TestForge/docs/SUITE_MINIMIZATION_REPORT.md).

---

### Criterion C14: Diff-Incremental CI/CD Mutation Hardening
- **Implementation**: [`testforge/diff_incremental.py`](file:///Users/sourabh/TestForge/testforge/diff_incremental.py) (`IncrementalHardeningEngine`, `parse_unified_diff_lines`).
- **Capabilities**:
  - Parses unified diff chunk headers (`@@ -l,s +start,count @@`) from git commits or PRs.
  - Restricts AST mutation operator injection exclusively to modified and added line numbers.
  - Across 4 realistic PR scenarios, eliminated **88.3% of redundant mutants** (240 down to 28), speeding up execution from 15.08s down to 2.80s (**5.39x macro speedup**) (with the caveat that non-local effects outside touched AST lines can escape, as reflected in [True, False, True, False] scenario detection).
- **Verification Tests**: [`tests/test_diff_incremental.py`](file:///Users/sourabh/TestForge/tests/test_diff_incremental.py) (3 passed).
- **Evidence Artifacts**: [`qa_artifacts/DIFF_INCREMENTAL_EVIDENCE.json`](file:///Users/sourabh/TestForge/qa_artifacts/DIFF_INCREMENTAL_EVIDENCE.json), [`docs/DIFF_INCREMENTAL_MODE.md`](file:///Users/sourabh/TestForge/docs/DIFF_INCREMENTAL_MODE.md).

---

### Criterion C15: Formal Invariant Synthesis & Bytecode Equivalence
- **Implementation**:
  - [`testforge/property_generator.py`](file:///Users/sourabh/TestForge/testforge/property_generator.py) (`PropertyTestGenerator` via Hypothesis `@given`).
  - [`testforge/equivalence.py`](file:///Users/sourabh/TestForge/testforge/equivalence.py) (`compare_bytecode_instructions`, `LLMEquivalenceJudge`).
- **Capabilities**:
  - Synthesizes formal property invariants using Hypothesis (boundedness, non-positivity, monotonicity, terminal state safety). Discovered **9 property-only mutation kills** on `order_fsm.py` (+8.5% score lift) that escaped nominal example-based assertions.
  - Normalizes and compares bytecode instructions via `dis.get_instructions` and recursively compares nested code objects. Achieved **100.0% precision, 0.0% false positive rate (0 non-equivalent false alarms), 90.0% recall, and 94.7% F1-score** on 30 ground-truth labeled benchmark mutants.
- **Verification Tests**: [`tests/test_hypothesis_property_testing.py`](file:///Users/sourabh/TestForge/tests/test_hypothesis_property_testing.py) (3 passed), [`tests/test_bytecode_and_llm_equivalence.py`](file:///Users/sourabh/TestForge/tests/test_bytecode_and_llm_equivalence.py) (4 passed).
- **Evidence Artifacts**: [`qa_artifacts/HYPOTHESIS_PROPERTY_EVIDENCE.json`](file:///Users/sourabh/TestForge/qa_artifacts/HYPOTHESIS_PROPERTY_EVIDENCE.json), [`docs/HYPOTHESIS_PROPERTY_TESTING.md`](file:///Users/sourabh/TestForge/docs/HYPOTHESIS_PROPERTY_TESTING.md), [`qa_artifacts/EQUIVALENCE_EVALUATION_REPORT.json`](file:///Users/sourabh/TestForge/qa_artifacts/EQUIVALENCE_EVALUATION_REPORT.json), [`docs/EQUIVALENCE_DETECTION_REPORT.md`](file:///Users/sourabh/TestForge/docs/EQUIVALENCE_DETECTION_REPORT.md).

