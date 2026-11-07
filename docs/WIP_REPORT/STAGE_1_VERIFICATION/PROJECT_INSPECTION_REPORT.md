# TestForge Stage 1: Project Inspection Report

**Inspection Date:** November 2, 2026  
**Repository Path:** `/Users/sourabh/TestForge`  
**Verified Commit SHA:** `ee8f765c4f7316e87439fab7250103e6da651c02`  
**Git Remote:** `https://github.com/sourabhJain121/Testforge.git`  
**Python Runtime:** `.venv-release` (Python 3.13.18 on macOS Darwin arm64)  
**Test Harness:** `pytest-9.1.1` (542 passed, 0 failed in full regression)  

---

## 1. Executive Summary of Inspection

A comprehensive static and dynamic inspection of the TestForge repository was conducted to establish verified empirical ground truth before generating the academic Work in Progress (WIP) Report. 

TestForge is an autonomous agentic test-hardening system designed to eliminate "illusory test coverage" by synthesizing value-aware unit tests guided by Abstract Syntax Tree (AST) mutation analysis. The codebase implements a decentralized multi-agent architecture where autonomous agents (Ingestion, Multi-Callable Generator, Adversarial Critic, Mutation Sandbox Evaluator, and Orchestrator) communicate through a thread-safe, partitioned in-memory and SQLite-persisted Blackboard pattern, the Agent-to-Agent (A2A) protocol (v0.3.0), and the Model Context Protocol (FastMCP).

---

## 2. Repository Layout & Component Taxonomy

The codebase contains 46,285+ additions across 536 tracked files, organized cleanly into core functional tiers:

```
TestForge/
├── testforge/                     # Core application package (39 modules)
│   ├── blackboard.py              # In-memory thread-safe shared context & pub/sub
│   ├── persistence.py             # SQLite WAL-mode checkpoint storage & resumption
│   ├── intelligent_generator.py   # Multi-callable AST analyzer & value-aware test synthesizer
│   ├── agents.py                  # Agent definitions, heuristics, and provider bridges
│   ├── adk_generator.py           # Google ADK agent framework integration
│   ├── adk_engine.py              # ADK session service & tool definitions
│   ├── crew_critic.py             # CrewAI adversarial mutation critic integration
│   ├── a2a.py                     # Agent-to-Agent message broker & Pydantic envelopes
│   ├── a2a_protocol.py            # Official A2A agent card & executor
│   ├── mcp_server.py              # FastMCP standardized tools (Filesystem & GitHub)
│   ├── mcp_client.py              # FastMCP client manager & Blackboard tool synchronizer
│   ├── mutator.py                 # AST-based mutation engine (9 operator families)
│   ├── sandbox.py                 # Subprocess test isolation & candidate test validator
│   ├── orchestrator.py            # Hardening lifecycle coordinator & state machine
│   ├── security.py                # AST security policy visitor & forbidden call blockers
│   ├── network_security.py        # SSRF blocker, IP parser & bounded streaming
│   ├── prompt_guard.py            # Indirect prompt-injection scanner & delimiter wraps
│   ├── callbacks.py               # Lifecycle event bus & scrubber
│   ├── logger.py                  # Telemetry JSONL structured trace logger
│   ├── diff_inspector.py          # Deterministic structural & semantic checkpoint differ
│   ├── ingestion.py               # Target source parser, module synthesizer & Git loader
│   ├── github_service.py          # Safe GitHub API client with rate-limiting
│   ├── benchmarking.py            # Multi-run empirical benchmark & ablation engine
│   └── websocket_hub.py           # WebSocket real-time event streaming hub
├── frontend/                      # Unified Web Cockpit (Single frontend tier)
│   ├── index.html                 # Semantic HTML5 cockpit with tabs & modal diagnostics
│   ├── style.css                  # Apple-inspired dark glassmorphism design system
│   └── app.js                     # Vanilla ES6 state controller & WebSocket listener
├── server.py                      # Production FastAPI application & REST/WebSocket routes
├── samples/                       # Target evaluation benchmarks & synthetic test fixtures
│   ├── discount.py                # Single-callable pricing benchmark (19 mutants)
│   └── uploaded_logistics_engine.py # Multi-callable logistics benchmark (258 mutants, 10 callables)
├── tests/                         # Full automated test suite (48 test files, 542 test cases)
├── qa_artifacts/                  # Independent empirical verification evidence & databases
│   ├── testforge_checkpoints.db   # Active production SQLite database (1,104 snapshots, 197 MB)
│   ├── phase2_test_generation_20261030_190423/    # Multi-callable implementation evidence
│   ├── phase3_independent_validation_20261031_142800/ # Deterministic reproduction evidence
│   └── phase4_final_readiness_20261031_144500/    # 16-step browser audit & screenshots
├── docs/                          # Comprehensive technical documentation & VIVA guides
│   ├── EVALUATION_PACKAGE/        # Handover documentation & acceptance checklists
│   ├── VIVA_PREPARATION/          # 12-document comprehensive academic defense package
│   └── WIP_REPORT/                # Work in Progress Report deliverables & evidence
├── Dockerfile                     # Multi-stage container deployment specification
├── docker-compose.yml             # Container orchestration with health checks
├── requirements.txt               # Pinned Python package dependencies
└── start_testforge.sh             # Executable shell launcher for FastAPI cockpit
```

---

## 3. Detailed Component Inspection

### 3.1 Multi-Callable AST Analysis & Intelligent Test Synthesis
- **Primary Module:** `testforge/intelligent_generator.py` (1,261 lines)
- **Key Classes:**
  - `IntelligentASTSynthesizer` (L332-L1261): Core test generation engine.
  - `ASTCallableAnalyzer` (L186-L325): Inspects AST comparison nodes (`visit_Compare`), assignments, and guards to extract boundary values (e.g. thresholds $-1, 0, 1$, comparison operators $<, \le, >, \ge$).
  - `ReferenceExecutor` (L111-L179): Safely compiles target code in memory and executes nominal inputs to record ground-truth return values and types.
- **Key Methods:**
  - `discover_callables(source_code)` (L339-L404): Discovers both standalone functions and class methods using AST parsing without executing arbitrary code.
  - `synthesize_test_suite(...)` (L491-L574): Generates 4 distinct test tiers: Nominal Happy Path, Boundary Value Analysis, Negative/Exception Guard Tests, and Mutation-Guided Refinements.
  - `_build_value_assertion(...)` (L1232-L1261): Inspects runtime return types to generate strict value assertions (`assert res == pytest.approx(expected)` for floats, exact equality for integers/booleans, and length/membership for collections).
- **Associated Test Suite:** `tests/test_ast_scope_extraction.py`, `tests/test_post_demo_defect_fixes.py`.

### 3.2 Shared State Management: The Blackboard Architecture
- **Primary Module:** `testforge/blackboard.py` (932 lines)
- **Key Classes:**
  - `Blackboard` (L208-L932): Thread-safe central state coordinator protected by an `RLock`.
  - Partitions: `TargetSpace` (L53-L67), `MutantSpace` (L70-L85), `CriticSpace` (L88-L94), `SuiteSpace` (L97-L109), `MetricsSpace` (L112-L134).
  - `BlackboardSubscription` (L163-L184): Pattern-matching pub/sub event subscription mechanism.
- **Key Methods:**
  - `update_partition(partition_name, data)` (L373-L495): Validates inputs against Pydantic partition schemas, increments atomic revision counter, notifies subscribers, and triggers optional SQLite auto-save.
  - `get_isolated_target_code()` (L303-L314): Thread-safe retrieval of ingested source.
- **Associated Test Suite:** `tests/test_blackboard.py` (18 tests), `tests/test_blackboard_persistence.py` (22 tests).

### 3.3 Persistence, Resumption & Differential Auditing
- **Primary Modules:** `testforge/persistence.py` (846 lines), `testforge/diff_inspector.py` (450 lines)
- **Key Classes:**
  - `SQLiteBlackboardStorage` (L176-L682): SQLite engine with WAL journaling (`PRAGMA journal_mode=WAL`), foreign key enforcement, and JSON serialization.
  - `DeterministicDiffInspector` (L100-L429): Computes fine-grained partition diffs between any two checkpoints, categorizing changes into ADDED, REMOVED, MODIFIED, and mutant status transitions (SURVIVED $\rightarrow$ KILLED).
- **Key Methods:**
  - `save_checkpoint(...)` (L272-L400): Serializes full state dictionary, hashes state payload, and writes to `blackboard_checkpoints` table.
  - `determine_resumption_plan(...)` (L694-L846): Determines stage skip logic to resume interrupted runs without re-executing already killed mutants.
- **Associated Test Suite:** `tests/test_checkpoint_resumption.py` (26 tests), `tests/test_checkpoint_diff.py` (8 tests).

### 3.4 Model Context Protocol (MCP) Integration
- **Primary Modules:** `testforge/mcp_server.py` (309 lines), `testforge/mcp_client.py` (658 lines)
- **Key Implementation:**
  - Official FastMCP framework (`mcp-python`).
  - `create_filesystem_server(sandbox_dir)` (L83-L172): Standardized filesystem tool server exposing `read_text_file`, `list_directory`, and `get_file_info` with path confinement.
  - `create_github_server(github_token)` (L175-L309): Standardized repository inspection server exposing `get_repository_info`, `get_file_contents`, and `search_repositories`.
  - `MCPClientManager` (L146-L584): Manages client connection, schema caching, input/output validation, and synchronization to the Blackboard `target_space`.
- **Associated Test Suite:** `tests/test_mcp.py` (22 tests), `tests/test_mcp_network_security.py` (12 tests), `tests/test_orchestration_mcp.py` (16 tests).

### 3.5 Agent-to-Agent (A2A) Protocol
- **Primary Modules:** `testforge/a2a.py` (659 lines), `testforge/a2a_protocol.py` (609 lines)
- **Key Implementation:**
  - A2A Protocol v0.3.0 compliance.
  - `A2ABroker` (L244-L659): In-process asynchronous message broker supporting FIPA-style performatives (`REQUEST`, `INFORM`, `AGREE`, `REFUSE`, `FAILURE`).
  - `build_testforge_agent_card()` (L98-L158): Generates official A2A JSON AgentCard describing capabilities, skills (`unit-test-generation`, `mutation-critique`, `hardening-workflow`), and transport modes (`JSONRPC`).
  - `TestForgeA2AExecutor` (L165-L609): Exposes standard A2A JSON-RPC 2.0 execution interface.
- **Associated Test Suite:** `tests/test_a2a.py` (16 tests), `tests/test_a2a_protocol.py` (15 tests), `tests/test_a2a_card_ui_and_endpoint.py` (5 tests).

### 3.6 Official Agent Frameworks: Google ADK & CrewAI
- **Google ADK Integration:** `testforge/adk_generator.py` (L31-L450) and `testforge/adk_engine.py` (L1-L260).
  - Uses `google-genai` / Google Agent Development Kit patterns (`LlmAgent`, `Runner`, `InMemorySessionService`, `BaseLlm`).
  - Encapsulates deliberate planning, tool binding, and test candidate generation.
- **CrewAI Integration:** `testforge/crew_critic.py` (L1-L320).
  - Uses `crewai` (`Agent`, `Task`, `Crew`, `BaseLLM`).
  - Configures an adversarial mutation critic role tasked with identifying surviving mutant AST diffs and issuing structured reflection directives.
- **Associated Test Suite:** `tests/test_adk_generator.py` (15 tests), `tests/test_crew_critic.py` (12 tests).

### 3.7 AST Mutation Engine
- **Primary Module:** `testforge/mutator.py` (458 lines)
- **Key Implementation:**
  - `MutationTransformer` (L37-L339): AST node visitor implementing 9 distinct mutation operator families:
    1. `ARITH_OP`: Arithmetic operators ($+ \leftrightarrow -, * \leftrightarrow /, // \leftrightarrow \%, ** \leftrightarrow *$).
    2. `COMP_OP`: Comparison operators ($< \leftrightarrow \le, > \leftrightarrow \ge, == \leftrightarrow \ne$).
    3. `BOUNDARY_SWAP`: Boundary thresholds ($< \leftrightarrow \le, > \leftrightarrow \ge$).
    4. `OFF_BY_ONE`: Off-by-one arithmetic increments/decrements ($+1, -1$).
    5. `COND_INV`: Boolean condition inversion (`if cond` $\leftrightarrow$ `if not cond`).
    6. `LOGICAL_CONN`: Logical connectors (`and` $\leftrightarrow$ `or`).
    7. `CONST_VAL`: Constant value modifications ($0 \leftrightarrow 1, True \leftrightarrow False$).
    8. `EXC_SWAP`: Exception type swapping (`ValueError` $\leftrightarrow$ `TypeError`).
    9. `RET_VAL`: Return value nullification or zeroing.
  - `ASTMutator` (L342-L458): Orchestrates mutant generation, produces isolated AST copies, and calculates AST unified diffs.
- **Associated Test Suite:** `tests/test_mutator.py`, `tests/test_ast_mutation_m2.py`, `tests/test_equivalent_mutants.py`.

### 3.8 Parallel Sandboxed Test Execution
- **Primary Module:** `testforge/sandbox.py` (931 lines)
- **Key Implementation:**
  - `ParallelSandboxRunner` (L174-L401): Evaluates mutant suites concurrently using `ThreadPoolExecutor` or `ProcessPoolExecutor`.
  - Process isolation: Every mutant is executed against candidate tests in an isolated temporary directory via `.venv-release/bin/python -m pytest` with strict execution timeouts (default 10s).
  - `GranularTestValidator` (L444-L931): AST validator ensuring generated test suites do not contain trivial assertions (e.g. `assert True`, `assert x is not None`) and only admits tests that achieve valid execution status.
- **Associated Test Suite:** `tests/test_sandbox.py`, `tests/test_cancellation.py`.

### 3.9 Multi-Layer Security Architecture
- **Primary Modules:** `testforge/security.py` (607 lines), `testforge/network_security.py` (318 lines), `testforge/prompt_guard.py` (344 lines)
- **Key Implementation:**
  - **AST Security Policy:** `_ASTSecurityVisitor` (L354-L607) scans source AST prior to compilation, blocking dangerous modules (`os`, `sys`, `subprocess`, `socket`, `shutil`), dangerous functions (`eval`, `exec`, `__import__`, `open`), and sensitive environment access.
  - **Network / SSRF Defense:** `SafeGitHubRedirectHandler` (L196-L253) and `validate_url_hostname` (L110-L193) enforce hostname whitelisting (`ALLOWED_GITHUB_HOSTS`), resolve DNS to detect private/loopback IP address ranges, and enforce 500 KB bounded reads (`bounded_read`).
  - **Prompt Defense:** `wrap_untrusted_content` (L84-L125) wraps ingested source code in cryptographic XML delimiter envelopes; `inspect_source_for_indirect_injections` (L128-L283) strips instruction-override keywords from comments and docstrings.
- **Associated Test Suite:** 98 dedicated security tests across `tests/test_security.py`, `tests/test_network_security.py`, `tests/test_mcp_network_security.py`, `tests/test_prompt_injection_defense.py`.

### 3.10 Production FastAPI Backend & Unified Web Cockpit
- **Backend Module:** `server.py` (1,751 lines)
  - 42 REST API endpoints + 1 WebSocket streaming hub.
  - Complete lifecycle routes: `/api/harden/start`, `/api/harden/status/{job_id}`, `/api/harden/cancel/{job_id}`, `/api/checkpoints/list`, `/api/checkpoints/diff`, `/api/a2a/test`, `/api/mcp/test`.
  - Health and discovery probes: `/healthz`, `/readyz`, `/.well-known/agent.json`.
- **Frontend Architecture:** `frontend/index.html` (75 KB), `frontend/app.js` (189 KB), `frontend/style.css` (54 KB)
  - Single-page application cockpit.
  - Zero heavy third-party framework runtime dependencies; pure native ES6 and WebSockets.
  - Real-time reactive updates, interactive diff viewer, checkpoint timeline, and diagnostic modals.

---

## 4. Inspection Verification Summary

| Dimension | Inspection Finding | Verification Status |
| :--- | :--- | :---: |
| **Codebase Size** | 39 modules in `testforge/`, 1,751 lines in `server.py`, 48 test files | **Verified** |
| **Commit Integrity** | HEAD at `ee8f765c4f7316e87439fab7250103e6da651c02`, working tree clean | **Verified** |
| **Regression Status** | 542 passed, 0 failed in 277 seconds | **Verified** |
| **Active SQLite DB** | `qa_artifacts/testforge_checkpoints.db` (197.3 MB, 1,104 snapshots) | **Verified** |
| **Runtime Health** | Backend running on port 8000; `/healthz` and `/readyz` returning HTTP 200 | **Verified** |

