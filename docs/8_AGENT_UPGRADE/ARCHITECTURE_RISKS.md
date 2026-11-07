# Architectural Risks, Compatibility Constraints & Invariants

**Project:** TestForge — Autonomous Agentic Unit Test Hardening System  
**Audit Date:** November 4, 2026  
**Auditor:** Principal AI Systems Architect & Evaluation Reviewer  
**Status:** FACTUAL AUDIT COMPLETED  

---

## 1. Framework Compatibility & Version Constraints

### 1.1 Google ADK (v1.14.1) vs. CrewAI (v1.15.28)

| Concern | Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **Telemetry & OTEL Conflict** | Both Google ADK and CrewAI attempt to configure OpenTelemetry tracers and exporters. CrewAI's automatic background telemetry can interfere with ADK streaming or produce stderr warnings. | **MEDIUM** | In [`testforge/crew_critic.py`](file:///Users/sourabh/TestForge/testforge/crew_critic.py), TestForge explicitly sets `os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"` and `os.environ["OTEL_SDK_DISABLED"] = "true"`. This isolation must be strictly preserved. |
| **Pydantic v2 Schema Constraints** | Both frameworks rely on Pydantic v2 (`pydantic>=2.7.0,<3.0.0`). However, CrewAI uses `output_pydantic` while Google ADK uses `output_schema`. Discrepancies in model serialization can cause validation errors. | **HIGH** | Use separate Pydantic model classes with strict typing for each framework (`GeneratedTestPayload` for ADK; `CriticDirectivePayload` for CrewAI). Broker messages between them using the neutral `A2AMessage` envelope. |
| **Duplicated Orchestration** | If CrewAI is given top-level task delegation (`allow_delegation=True`), it attempts to resolve its own agent hierarchy, colliding with Google ADK's `Runner` / `Supervisor`. | **CRITICAL** | **Architectural Invariant:** CrewAI `Agent` must always have `allow_delegation=False`. CrewAI is strictly an in-memory specialist task invoked via the A2A broker, never a top-level runner. |

---

## 2. Concurrency, Async/Sync & Runtime Execution Risks

### 2.1 Asyncio vs. Multiprocess Sync Pytest Execution
- **The Issue:**
  - Google ADK (`LlmAgent`, `Runner`) and FastMCP (`ClientSession`, `stdio_client`) are asynchronous (`asyncio`).
  - Pytest test execution and mutation evaluation in `ParallelSandboxRunner` are synchronous and multiprocess (`concurrent.futures.ProcessPoolExecutor` running Python subprocesses).
- **The Risk:**
  Calling blocking subprocesses or thread pool waits directly inside an active asyncio event loop blocks the loop, causing WebSockets, HTTP requests, or FastMCP stdio pipes to time out or deadlock.
- **The Mitigation:**
  Use `asyncio.to_thread` or execute sandbox operations within a dedicated background worker thread pool (`ThreadPoolExecutor`), maintaining strict separation between the async ADK event loop and synchronous sandbox workers.

### 2.2 Blackboard State Consistency & Concurrency
- **The Risk:**
  As the number of agents increases from 3 to 8, concurrent reads and writes to the Blackboard could cause race conditions or state corruption.
- **The Mitigation:**
  - Maintain the existing `threading.RLock()` protecting all partition mutations.
  - Enforce deep-copy isolation on reads (`copy.deepcopy`), ensuring no agent can mutate shared state in place without going through `blackboard.update_*_space()`.
  - Maintain SQLite Write-Ahead Logging (WAL) with transactional commits on every partition update.

---

## 3. Security & Sandboxing Risks

| Risk Area | Threat Vector | Existing Countermeasure | 8-Agent Enhancement |
| :--- | :--- | :--- | :--- |
| **Prompt Injection into Critic** | Target source code or test docstrings contain indirect prompt-injection instructions attempting to hijack the Critic. | `prompt_guard.py` AST scanner defuses injections by replacing them with `[DEFUSED_PROMPT_INJECTION]`. | Dedicated **Security Agent** inspects all prompts and tool arguments before delivery to Critic. |
| **Sandbox Execution Escape** | Generated test code imports `subprocess`, `os.system`, or opens network sockets to escape the test harness. | `CodeSanitizer` and `SecurityGuardrail.inspect_ast` block dangerous AST primitives. | The **Security Agent** must perform pre-flight AST validation before passing tests to the **Test Execution Agent**. |
| **Filesystem Traversal** | Agent uses FastMCP `read_text_file` with `../../` to exfiltrate host credentials. | `_is_path_safe` resolves paths against permitted root and blocks `.env` / keys. | Maintain strict permitted root jails; whitelist only read-only FastMCP tools. |

---

## 4. Protected Components (MUST NOT BE REWRITTEN)

The following core components represent highly stabilized, hardware-tuned, and empirically verified subsystems. They **must be preserved and reused as foundation building blocks** without architectural rewrites:

1. **`ParallelSandboxRunner` ([`testforge/sandbox.py:196`](file:///Users/sourabh/TestForge/testforge/sandbox.py#L196)):**
   Hardware-tuned for Apple Silicon M2 Pro (10 cores, 8 parallel workers), ephemeral temp directory isolation, 5-second process timeout guards, and JSON coverage parsing. Must NOT be rewritten.
2. **`ASTMutator` ([`testforge/mutator.py:150`](file:///Users/sourabh/TestForge/testforge/mutator.py#L150)):**
   Deterministic fault injection covering comparison, arithmetic, and logical boundary inversions.
3. **`SQLiteBlackboardStorage` ([`testforge/persistence.py:65`](file:///Users/sourabh/TestForge/testforge/persistence.py#L65)):**
   ACID-compliant WAL SQLite storage with snapshot serialization and SHA-256 data validation.
4. **`HardwareAccelerator` (`hw_profile` in [`testforge/accel.py`](file:///Users/sourabh/TestForge/testforge/accel.py)):**
   Apple Silicon M-series hardware topology detection and thread allocation.
5. **`FastMCP Server Implementations` ([`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py)):**
   Standard FastMCP server definitions for filesystem and repository tools.

