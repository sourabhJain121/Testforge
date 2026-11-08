# TestForge: Autonomous Agentic Unit Test Hardening System

> **Course**: CSE3101 - Agentic AI (16 Weeks, Phase-3 Final Evaluation)  
> **Authors**: Sourabh & Shreshth  
> **Target Platform**: macOS (Apple Silicon M-Series Optimized, arm64) & Linux Container  
> **Repository**: [sourabhJain121/Testforge](https://github.com/sourabhJain121/Testforge)  
> **Dual-Framework Agentic Core**: Google ADK v1.14.1 + CrewAI via Official A2A Wire Protocol (v0.3.0)  
> **Storage & Protocol**: SQLite WAL Checkpoints, Model Context Protocol (FastMCP), W3C OpenTelemetry Traces  

---

## 1. Executive Summary

**TestForge** is an enterprise-grade autonomous multi-agent software engineering platform that automatically discovers, diagnoses, and hardens weak unit test suites for Python applications. While traditional continuous integration pipelines measure superficial **statement/line coverage** (a metric trivially satisfied by hollow tests that execute code paths without verifying state or boundaries), TestForge formulates software verification as an **adversarial multi-agent consensus game**.

TestForge unifies **Google Agent Development Kit (ADK)** for primary stateful orchestration with **CrewAI** for adversarial test quality critique, coordinated over an **Official Agent2Agent (A2A v0.3.0)** wire protocol. The system pairs deterministic **Abstract Syntax Tree (AST) fault injection**, **isolated subprocess and real Docker container sandboxing**, **SQLite WAL transactional checkpoints**, and **bytecode instruction normalization** to eliminate test suite vulnerabilities and drive mutation kill scores to mathematical limits.

```mermaid
flowchart TD
    subgraph INGEST["1. Ingestion & AST Analysis (Google ADK TargetManagerAgent)"]
        A1["Mode A: Local Filesystem / Upload"] --> B["AST Static Inspector & Call Graph Visitor"]
        A2["Mode B: AI Natural Language Synthesis"] --> B
        A3["Mode C: Direct GitHub URL Fetch"] --> B
        B --> BR["Blast Radius & Dependency Risk Analyzer"]
    end

    subgraph ADK_ORCH["2. Stateful Blackboard & Google ADK Orchestrator"]
        BR --> BB[("SQLite WAL Persistent Blackboard<br/>8 Partitioned Spaces")]
        BB <--> SUP["SupervisorAgent (Google ADK Runner)"]
        SUP --> PLAN["TestPlanningAgent (Google ADK)"]
        PLAN --> GEN["TestGeneratorAgent (Google ADK)"]
    end

    subgraph SANDBOX["3. Subprocess & Docker Sandboxing"]
        GEN --> SB["Subprocess / Docker Sandbox<br/>(--network none, 5.0s Timeout)"]
        SB -->|Pass@1 Clean Check| MUT["Deterministic AST Mutator<br/>(10 Mutation Operator Classes)"]
        SB -.->|Syntax Violation| REP["ReflectionRepairAgent (Google ADK)"]
        REP -.-> SB
    end

    subgraph CRITIC["4. Distributed Adversarial Critic (CrewAI & A2A)"]
        MUT --> PAR["ProcessPoolExecutor (Parallel Sandbox)"]
        PAR -->|Surviving Mutant AST Diffs| A2A_WIRE["A2A Protocol Broker (v0.3.0)<br/>Cross-Process JSON-RPC"]
        A2A_WIRE --> CRIT["MutationQualityCriticAgent (CrewAI)"]
        CRIT -->|Prescriptive Directives| BB
    end

    subgraph VERIFY["5. Formal Verification & Suite Optimization"]
        BB --> HYP["Hypothesis Property Generator (@given)"]
        BB --> EQ["Bytecode Equivalence Judge (dis AST + LLM)"]
        BB --> MIN["TestSuiteMinimizer (Greedy Set Cover)"]
        MIN --> EXP["Export Standalone Suite (test_hardened.py)<br/>+ JUnit XML & OASIS SARIF v2.1.0"]
    end

    subgraph OBS["6. Telemetry & Governance"]
        PAR -.-> OTEL["OpenTelemetry Distributed Tracing (W3C)"]
        CRIT -.-> OTEL
        EXP --> GATE["Human Approval Gate (Repo Writes & PRs)"]
    end
```

---

## 2. Handout Requirements Traceability Matrix

Every requirement from the Coursework Specification (Features F1 through F9) and Phase-3 Evaluation Rubric (C11 through C15) is implemented in clean production code and verified with empirical regression suites:

| Handout Feature | Architectural Capability | Production Source File | Verification Test Suite | Status |
| :--- | :--- | :--- | :--- | :---: |
| **F1** | 8-Partition Atomic Blackboard Architecture | [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py) | [`tests/test_blackboard.py`](file:///Users/sourabh/TestForge/tests/test_blackboard.py) | **PASS** |
| **F2** | Dual Agentic Framework (Google ADK + CrewAI) | [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py), [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py) | [`tests/test_adk_production_path.py`](file:///Users/sourabh/TestForge/tests/test_adk_production_path.py) | **PASS** |
| **F3** | Agent2Agent (A2A) Official Wire Protocol v0.3.0 | [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py), [`testforge/a2a_protocol.py`](file:///Users/sourabh/TestForge/testforge/a2a_protocol.py) | [`tests/test_a2a_protocol.py`](file:///Users/sourabh/TestForge/tests/test_a2a_protocol.py) | **PASS** |
| **F4** | ADK Deliberation, Callbacks & Output Guardrails | [`testforge/adk_callbacks.py`](file:///Users/sourabh/TestForge/testforge/adk_callbacks.py), [`testforge/security.py`](file:///Users/sourabh/TestForge/testforge/security.py) | [`tests/test_adk_callbacks.py`](file:///Users/sourabh/TestForge/tests/test_adk_callbacks.py) | **PASS** |
| **F5** | FastMCP Client & Stdio Filesystem Server | [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py), [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py) | [`tests/test_testforge_mcp_server.py`](file:///Users/sourabh/TestForge/tests/test_testforge_mcp_server.py) | **PASS** |
| **F6** | OpenTelemetry W3C Tracing & Telemetry | [`testforge/observability.py`](file:///Users/sourabh/TestForge/testforge/observability.py), [`testforge/logger.py`](file:///Users/sourabh/TestForge/testforge/logger.py) | [`tests/test_observability.py`](file:///Users/sourabh/TestForge/tests/test_observability.py) | **PASS** |
| **F7** | Persistent Checkpoint Timeline & Semantic Diff | [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py), [`testforge/checkpoint_diff.py`](file:///Users/sourabh/TestForge/testforge/checkpoint_diff.py) | [`tests/test_checkpoint_diff.py`](file:///Users/sourabh/TestForge/tests/test_checkpoint_diff.py) | **PASS** |
| **F8** | Subprocess & Live Docker Sandbox Backend | [`testforge/sandbox.py`](file:///Users/sourabh/TestForge/testforge/sandbox.py), [`testforge/docker_sandbox.py`](file:///Users/sourabh/TestForge/testforge/docker_sandbox.py) | [`tests/test_sandbox_backend.py`](file:///Users/sourabh/TestForge/tests/test_sandbox_backend.py) | **PASS** |
| **F9** | Standalone CLI, Containerization & CI/CD Probes | [`testforge/cli.py`](file:///Users/sourabh/TestForge/testforge/cli.py), [`server.py`](file:///Users/sourabh/TestForge/server.py) | [`tests/test_production_packaging_and_cli.py`](file:///Users/sourabh/TestForge/tests/test_production_packaging_and_cli.py) | **PASS** |
| **C11** | Zero-Egress Privacy Mode & PII Scrubbing | [`testforge/privacy_mode.py`](file:///Users/sourabh/TestForge/testforge/privacy_mode.py) | [`tests/test_privacy_mode.py`](file:///Users/sourabh/TestForge/tests/test_privacy_mode.py) | **PASS** |
| **C12** | Multimodal Vision FSM Requirement Derivation | [`testforge/multimodal_fsm.py`](file:///Users/sourabh/TestForge/testforge/multimodal_fsm.py) | [`tests/test_multimodal_fsm.py`](file:///Users/sourabh/TestForge/tests/test_multimodal_fsm.py) | **PASS** |
| **C13** | Greedy Set Cover Test Suite Minimizer | [`testforge/minimizer.py`](file:///Users/sourabh/TestForge/testforge/minimizer.py) | [`tests/test_suite_minimizer.py`](file:///Users/sourabh/TestForge/tests/test_suite_minimizer.py) | **PASS** |
| **C14** | Diff-Incremental Targeted Fault Mutation | [`testforge/diff_incremental.py`](file:///Users/sourabh/TestForge/testforge/diff_incremental.py) | [`tests/test_diff_incremental.py`](file:///Users/sourabh/TestForge/tests/test_diff_incremental.py) | **PASS** |
| **C15** | Formal Hypothesis Property Invariants (`@given`) | [`testforge/property_generator.py`](file:///Users/sourabh/TestForge/testforge/property_generator.py) | [`tests/test_hypothesis_property_testing.py`](file:///Users/sourabh/TestForge/tests/test_hypothesis_property_testing.py) | **PASS** |

---

## 3. Real Tool & Dependency Versions

All dependencies are pinned in `pyproject.toml` and verified in `.venv-release`:

| Tool / Framework | Verified Version | Role in Architecture |
| :--- | :---: | :--- |
| **Python** | `3.13.18` | Base runtime environment (CPython aarch64 Apple Silicon) |
| **google-adk** | `1.14.1` | Primary agent framework (Runners, Sessions, Memory, Callbacks) |
| **crewai** | `0.102.0` | Specialist framework for Adversarial Mutation Quality Critique |
| **mutmut** | `3.8.1` | External mutation testing judge for cross-engine score validation ($r=0.9988$) |
| **hypothesis** | `6.170.15` | Property-based fuzzing and invariant assertion generation |
| **opentelemetry-sdk** | `1.39.1` | W3C distributed tracing and span export |
| **fastapi** | `0.128.8` | Production asynchronous ASGI server and REST / WS endpoints |
| **uvicorn** | `0.42.0` | Production ASGI web server running on port 8000 |
| **playwright** | `1.58.0` | Headless Chromium browser automation and DOM verification |
| **docker** | `29.4.3` | Native kernel container sandboxing (`--network none`) |
| **pydantic** | `2.12.5` | Type validation and Blackboard schema enforcement |
| **pytest** | `9.1.1` | Master test runner orchestrating 870+ regression tests |

---

## 4. Single Source of Truth Empirical Benchmarks

The official multi-target evaluation results derive end-to-end from pipeline execution, recorded in `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json` across 3 seeds (`[42, 43, 44]`):

### Cross-Target Benchmark Performance Summary (n=3 Seeds)

| Evaluation Scenario | Mean Line Cov % | Mean Branch Cov % | Arithmetic Mean Raw MS % | Geometric Mean Raw MS % | Adjusted Mean MS % | Mean Latency (s) | Total Tokens | Mutants Killed / Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Minimal Tests)** | 30.75% | 25.62% | 6.46% | 6.42% | 6.79% | 0.06s | 0 | 16 / 240 |
| **Zero-Shot LLM** | 39.17% | 30.48% | 32.58% | 27.82% | 34.33% | 1.66s | 2,660 | 58 / 240 |
| **TestForge Agentic Reflection** | **70.58%** | **65.65%** | **67.02%** | **59.91%** | **70.17%** | **14.89s** | **10,650** | **167 / 240** |
| **Relative Lift vs Baseline** | **+39.83%** | **+40.03%** | **+60.56%** | **+53.49%** | **+63.38%** | - | - | **+151 Kills** |
| **Relative Lift vs Zero-Shot** | **+31.41%** | **+35.17%** | **+34.44%** | **+32.09%** | **+35.84%** | - | - | **+109 Kills** |

### Per-Target Breakdown (TestForge Autonomous Pipeline)

| Target Module | LOC | Callables | Mutants | Line Cov % | Branch Cov % | Raw MS % | Adjusted MS % | Equivalent Excluded | Mutants Killed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`samples/discount.py`** | 19 | 1 | 19 | 100.0% | 100.0% | **94.74%** | **100.0%** | 1 | 18 / 19 |
| **`samples/order_fsm.py`** | 98 | 9 | 106 | 82.20% | 75.00% | **97.17%** | **100.0%** | 3 | 103 / 106 |
| **`samples/lru_cache.py`** | 34 | 4 | 42 | 52.50% | 43.80% | **30.95%** | **34.21%** | 4 | 13 / 42 |
| **`samples/stats_calculator.py`** | 68 | 5 | 73 | 47.60% | 43.80% | **45.21%** | **46.48%** | 2 | 33 / 73 |
| **Macro Average** | **54.8** | **4.8** | **60.0** | **70.58%** | **65.65%** | **67.02%** | **70.17%** | **2.5** | **167 / 240** |

---

## 5. Quickstart & One-Command Demo

### Prerequisites
- macOS Apple Silicon (arm64) or Linux x86_64 / aarch64
- Python 3.11 - 3.13 (Production reference: Python 3.13.18)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/sourabhJain121/Testforge.git
cd TestForge

# 2. Activate virtual environment
source .venv-release/bin/activate

# 3. Install dependencies in editable mode
pip install -e .
```

### Run the Interactive Web Dashboard
Launch the unified FastAPI server and dashboard cockpit:
```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
- **Dashboard Cockpit**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **OpenAPI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **A2A Agent Card Discovery**: [http://127.0.0.1:8000/.well-known/agent-card.json](http://127.0.0.1:8000/.well-known/agent-card.json)
- **FastMCP Tool Status**: [http://127.0.0.1:8000/api/mcp/status](http://127.0.0.1:8000/api/mcp/status)
- **Liveness & Readiness Probes**: [http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz) | [http://127.0.0.1:8000/readyz](http://127.0.0.1:8000/readyz)

### Standalone Command-Line Interface (CLI)

```bash
# 1. Standard Autonomous Hardening
python -m testforge.cli harden samples/discount.py \
  --max-iter 3 \
  --target-score 85.0 \
  --engine-mode auto \
  --output test_hardened.py

# 2. Zero-Egress Privacy Mode (Air-Gapped Local Ollama Execution)
python -m testforge.cli harden samples/discount.py \
  --privacy-mode \
  --engine-mode local \
  --output test_hardened_private.py

# 3. Diff-Incremental PR Hardening (Mutate only lines modified in git diff)
python -m testforge.cli diff samples/discount.py --diff-file my_pr.diff

# 4. Greedy Set Cover Test Suite Minimization
python -m testforge.cli minimize samples/discount.py --test-file qa_artifacts/test_hardened_discount.py
```

---

## 6. Beyond the Handout: Advanced Capabilities

TestForge implements 6 cutting-edge software engineering capabilities beyond the original coursework mandate:

1. **Zero-Egress Privacy Mode (`testforge/privacy_mode.py`)**:
   - Enforces an air-gapped security boundary by monkeypatching low-level OS sockets (`ZeroEgressSocketInterceptor`).
   - Intercepts 100% of outbound external TCP network calls while preserving local loopback IPC (`127.0.0.1:11434` for Ollama).
   - Sanitizes 7 categories of PII and API tokens (Gemini, OpenRouter, GitHub, emails, SSNs) prior to model invocation.

2. **Multimodal Vision FSM Requirement Derivation (`testforge/multimodal_fsm.py`)**:
   - Synthesizes robust unit test suites directly from visual architectural state machine diagrams (`tests/fixtures/fsm_diagram.png`).
   - Uses Gemini Vision with an offline deterministic topology parser fallback. Achieves **74.5% raw mutation kill score (79/106 kills)** out-of-the-box from visual diagram inputs alone.

3. **Greedy Set Cover Test Suite Minimization (`testforge/minimizer.py`)**:
   - Analyzes the 2D Boolean Kill Matrix ($T \times M$) to solve the classic NP-hard set cover problem using greedy approximation.
   - Evaluated across 4 canonical benchmark modules: compresses test suite from 134 tests down to 28 tests (**79.1% macro reduction**) with **strictly 100.0% mutation score retention** (0 dropped kills).

4. **Diff-Incremental CI/CD Mutation Mode (`testforge/diff_incremental.py`)**:
   - Extracts modified and added line numbers from unified git diffs (`git diff -U0`).
   - Restricts AST mutation operator injection exclusively to modified lines. Eliminates **88.3% of redundant mutants** (240 down to 28), accelerating CI runtime by **5.39x (15.08s down to 2.80s)** while confining mutation analysis strictly to PR change boundaries.

5. **Recursive Bytecode Instruction Normalization (`testforge/equivalence.py`)**:
   - Disassembles AST mutants using Python's `dis` module and recursively normalizes bytecode instructions to detect compilation-equivalent mutants.
   - Evaluated against 30 ground-truth labeled mutants: achieved **100.0% precision, 0.0% false positive rate (0 non-equivalent false alarms), 90.0% recall, and 94.7% F1-score**.

6. **Hypothesis Property-Based Assertion Synthesis (`testforge/property_generator.py`)**:
   - Synthesizes formal mathematical property invariants using the Hypothesis library (`@given(st.floats(...))`).
   - Discovered **9 property-only mutation kills** on `order_fsm.py` (+8.5% score lift) that escaped nominal example-based assertions.

---

## 7. Verification & Regression Test Suite

TestForge maintains an exhaustive automated regression suite covering all architectural layers:

```bash
# Run the complete test suite (870+ tests across 90+ test files)
CREWAI_TESTING=true CREWAI_TRACING_ENABLED=false pytest tests/ -q

# Run fast execution profile using xdist workers
python testforge/scripts/run_tests.py --profile fast

# Run live browser headless verification across all 12 dashboard views
python testforge/scripts/capture_frontend_evidence.py
```

### Test Suite Directory Layout (870+ Tests Passing)
- **`tests/test_a2a*.py`** (37 tests): Official A2A v0.3.0 wire protocol, AgentCard discovery, and cross-process workers.
- **`tests/test_adk*.py`** (52 tests): Google ADK Runners, Sessions, Memory, Web compatibility, and Callbacks.
- **`tests/test_blackboard*.py`** (52 tests): 8-partition atomic Blackboard, SQLite WAL transaction logs, and checkpoint diffing.
- **`tests/test_mutator*.py` & `tests/test_ast*.py`** (46 tests): 10-class deterministic AST mutator passes, diff targeting, and operator diversity.
- **`tests/test_sandbox*.py`** (17 tests): Subprocess isolation, timeout defense, and real Docker daemon sandboxing.
- **`tests/test_privacy_mode.py`** (6 tests): Zero-egress socket interception and secret/PII sanitization.
- **`tests/test_multimodal_fsm.py`** (5 tests): Vision-based diagram requirement derivation.
- **`tests/test_suite_minimizer.py`** (4 tests): Greedy set cover suite compression and kill matrix calculation.
- **`tests/test_diff_incremental.py`** (3 tests): Git diff hunk parsing and focused mutant injection.
- **`tests/test_flaky_detection.py`** (3 tests): Non-deterministic seed re-runs and flaky test quarantine.
- **`tests/test_bytecode_and_llm_equivalence.py`** (4 tests): Bytecode instruction comparison and equivalent mutant classification.
- **`tests/test_hypothesis_property_testing.py`** (3 tests): Property test synthesis with `@given`.
- **`tests/test_guardrails_approval.py`** (6 tests): AST network/import blocking and Human Approval Gate.
- **`tests/test_frontend_playground_verification.py`** (9 tests): Headless Playwright Chrome execution across all dashboard panes.

---

## 8. License

Developed for **CSE3101: Agentic AI** coursework by **Sourabh** & **Shreshth**.  
Licensed under the Apache 2.0 License.
