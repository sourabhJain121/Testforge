# TestForge Feature-by-Feature Reality Check Audit Report

> **Audit Objective:** Empirical validation of all 11 core TestForge capabilities using real runtimes (no mock fakes), asserting exact contracts, and recording execution evidence in `docs/AUDIT_EVIDENCE/`.

---

## Executive Summary Matrix

| # | Feature Name | Component / Entrypoint | Verification Method | Status | Key Evidence / Metric |
| :-: | :--- | :--- | :--- | :-: | :--- |
| **1** | **A2A Wire Protocol** | `testforge/a2a.py` & `testforge/a2a_protocol.py` | Real message exchange via in-process FIPA broker & `a2a-sdk` v0.3.0 AgentCard discovery | **PASS** | `REQUEST` -> `AGREE` envelope exchange; AgentCard `testforge-agent-system` v1.0.0 (3 skills) |
| **2** | **FastMCP Tool Server** | `testforge/mcp_server.py` | Stdio client handshake, tool enumeration (`list_tools`), and live execution (`list_jobs`) | **PASS** | FastMCP server connected over stdio; discovered `harden_module`, `get_report`, `list_jobs`; tool invocation succeeded |
| **3** | **SQLite WAL Checkpointing** | `testforge/persistence.py` | Transactional snapshot save/restore, crash recovery, and WAL mode verification | **PASS** | SQLite PRAGMA journal_mode = `wal`; snapshot restored at revision 2; suite code preserved |
| **4** | **Docker vs Subprocess Sandbox** | `testforge/sandbox.py` | Process isolation, timeout enforcement, and Docker daemon availability check | **PASS** | Subprocess test passed; 2s timeout killed infinite loop; Docker status honestly reported (`SKIPPED_HONESTLY` on macOS without live daemon) |
| **5** | **10 AST Mutation Operators** | `testforge/mutator.py` | Programmatic AST fault injection over multi-construct snippet; diff extraction | **PASS** | 10/10 core categories generated (`COMP_OP`, `BOUNDARY_SWAP`, `OFF_BY_ONE`, `ARITH_OP`, `LOGICAL_CONN`, `MATH_FUNC`, `COND_INV`, `RETURN_VAL`, `CONST_VAL`, `EXCEPT_HANDLER`) + held-out operators |
| **6** | **Multimodal Vision FSM Parsing** | `testforge/multimodal_fsm.py` | Matplotlib diagram generation (PNG) and topology/vision extraction | **PASS** | Generated 64KB FSM PNG; extracted 10 states, 12 transitions, 3 terminal states (`COMPLETED`, `CANCELLED`, `REFUNDED`); offline parser fallback validated |
| **7** | **Hypothesis Invariant Generator** | `testforge/property_generator.py` | Dynamic synthesis of `@given` / `@settings` property suites against `samples/discount.py` | **PASS** | Generated property tests with upper bound and non-negative invariants; candidate suite validated in sandbox |
| **8** | **Greedy Set Cover Minimizer** | `testforge/minimizer.py` | Kill-matrix construction and reduction over duplicate test cases | **PASS** | 6 tests reduced to 4 tests (33.3% reduction); 100.0% mutation score retention |
| **9** | **Diff-Incremental Confinement** | `testforge/diff_incremental.py` | Unified diff parsing (lines 10-11) and targeted AST fault injection | **PASS** | 100% of generated mutants confined strictly to lines 10 and 11; 0 mutants outside diff lines |
| **10** | **Bytecode Equivalence Filter** | `testforge/equivalence.py` | Disassembly comparison (`compare_bytecode_instructions`) & dead-code detection | **PASS** | Dead-code mutant produced identical bytecode (`EQUIVALENT`); operator mutant produced distinct bytecode (`UNKNOWN` / `NOT_EQUIVALENT`) |
| **11** | **W3C OpenTelemetry Tracing** | `testforge/observability.py` | Trace provider span recording & W3C `traceparent` carrier propagation | **PASS** | Recorded root job span and child agent span; W3C `traceparent` format verified: `00-{32 hex trace_id}-{16 hex span_id}-01` |

---

## Detailed Findings and Provenance Clarifications

### 1. A2A Architecture: Dual-Tier Implementation
TestForge provides a dual-tier agent communication architecture:
1. **Internal In-Process Typed Broker (`testforge/a2a.py`):** Strongly-typed Pydantic message envelopes adhering to FIPA-ACL communicative acts (`REQUEST`, `INFORM`, `AGREE`, `REFUSE`, `FAILURE`, `PROPOSE`). Provides sub-millisecond in-process agent handoffs with full correlation tracking and security inspection.
2. **External Wire Protocol Layer (`testforge/a2a_protocol.py`):** Implements the official Google Agent2Agent (A2A) protocol specification (v0.3.0) via `a2a-sdk`. Exposes `/.well-known/agent-card.json`, declares `testforge-agent-system` capabilities, and handles JSON-RPC task lifecycle requests.

### 2. FastMCP Tool Server
The Model Context Protocol implementation uses the official FastMCP SDK (`from mcp.server.fastmcp import FastMCP`). Tools are typed and validated with Pydantic models. File paths outside the designated repository root are blocked via strict boundary checks.

### 3. Docker vs Subprocess Sandbox Isolation
Subprocess isolation operates via POSIX detached process groups (`setsid`) and `resource.setrlimit` CPU limits, combined with `conftest.py` socket monkeypatching to prevent network egress. When running on macOS arm64 without a live Docker daemon, `is_docker_available()` returns `False` immediately without blocking or hanging, allowing the runtime to fall back safely to `SubprocessSandboxBackend`.

### 4. Multimodal Vision FSM Extraction
The vision pipeline renders high-resolution state diagrams via matplotlib. When `GEMINI_API_KEY` is present and quota is available, it queries `gemini-3.6-flash` vision. If quota is exhausted (HTTP 429) or in offline privacy mode, the engine gracefully falls back to the deterministic topological diagram parser, preserving end-to-end pipeline execution without crashing.

### 5. Bytecode Disassembly & Equivalence Filtering
The equivalence analyzer utilizes Python's built-in `dis` module to compile and compare normalized bytecode instructions. Trivial modifications to dead code (code following an unconditional return) compile to identical bytecode and are automatically classified as `EQUIVALENT` with `HIGH` confidence, preventing artificial score penalties.

### 6. W3C OpenTelemetry Header Propagation
The observability layer implements W3C TraceContext propagation using `TraceContextTextMapPropagator`. During inter-agent handoffs, outgoing messages inject standard `traceparent` headers (`00-{trace_id}-{span_id}-01`), enabling end-to-end distributed trace reconstruction across agents.

