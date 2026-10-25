# TestForge Phase 1 — Milestone 1.2: Real MCP Tool Invocation in the Autonomous Agent Workflow (GAP-02)

## Executive Summary
Milestone 1.2 successfully resolves **GAP-02** ("Real MCP Tool Invocation in the Autonomous Agent Workflow") by replacing disconnected/simulated tool paths with end-to-end FastMCP stdio transport tool execution, typed Pydantic contract validation, deterministic tool selection, deep downstream agent pipeline integration, lifecycle observability, and fault isolation.

All 14 specified milestone criteria have been implemented and validated against the actual TestForge runtime with zero mock shortcuts.

---

## Architecture & Implementation Overview

### 1. Typed Pydantic Schema Contracts
In `testforge/mcp_client.py`, every registered FastMCP tool is bound to strongly typed input and output Pydantic models:
- `ReadTextFileInput` (`path: str`)
- `GetFileInfoInput` (`path: str`)
- `GetFileInfoOutput` (`path: str`, `is_file: bool`, `is_dir: bool`, `size_bytes: int`, `line_count: int`, `sha256: str`)
- `ListDirectoryInput` (`path: str = "."`)
- `GetRepositoryInfoInput` (`repo: str`)
- `GetRepositoryInfoOutput` (`name: str`, `owner: str`, `stars: int`, `forks: int`, `default_branch: str`)
- `ToolSelectionDecision` (`tool_name: Optional[str]`, `arguments: Dict[str, Any]`, `reason: str`, `should_invoke: bool`)

### 2. Pre-Invocation Argument Validation & Post-Invocation Schema Checking
- `MCPClientManager._validate_arguments`: Validates invocation arguments against `TOOL_INPUT_MODELS` before launching stdio subprocesses. Emits a `VALIDATION_FAILURE` event on malformed or missing fields.
- `MCPClientManager._validate_response`: Validates raw server payloads against expected output contracts, transparently converting non-conforming responses into `MalformedToolResponse` models to prevent unhandled pipeline exceptions.

### 3. Deterministic Tool Selection Policy
Implemented via `resolve_mcp_tool_need()` in `testforge/orchestrator.py`:
- **File path given without source code**: Returns `ToolSelectionDecision(tool_name="read_text_file", should_invoke=True)`.
- **File path and source code both given**: Returns `ToolSelectionDecision(tool_name="get_file_info", should_invoke=True)` to verify file hash and provenance.
- **In-memory source code only (no file path)**: Returns `ToolSelectionDecision(should_invoke=False)` with zero unnecessary overhead.

### 4. Downstream Agent Pipeline Consumption
During `TaskLifecycleState.INGESTING`:
- When source code is retrieved via `read_text_file`, it is inspected for prompt injection by `SecurityGuardrail.inspect_input(content, source="mcp:read_text_file")`.
- If valid, the code is parsed into AST function representations (`extract_ast_nodes`), registered in the Blackboard `target_space` partition (`source_sha`, `line_count`, `mcp_tool_called`), saved in SQLite checkpoints, and propagated into test generation agent prompts (`LLMClient.generate_tests_for_code`).

### 5. Lifecycle Observability & Secret Redaction
- Invocations trigger `CallbackRegistry.dispatch(EventType.TOOL_START)` and `EventType.TOOL_COMPLETE`.
- In `invoke_mcp_tool()`, `TraceLogger.log_trace()` records `MCP_TOOL_START` and `MCP_TOOL_COMPLETE` with stage name, duration, and scrubbed summaries.
- `redact_sensitive_data()` defensibly redacts passwords, tokens, API keys, and sensitive fields across dicts, strings, and tool arguments.

### 6. Fault Isolation & Session Management
- **Timeouts**: Handled with clean cancellation without deadlocking the asyncio loop.
- **Missing Tools & Server Crashes**: Handled cleanly with `McpError` isolation.
- **Security Boundaries**: Path traversal (`../`) and access to credential patterns (`.env`, `id_rsa`) are rejected prior to execution.
- **Disconnection**: `MCPClientManager.disconnect_sync()` and `disconnect()` ensure stdio child processes are cleanly closed, preventing cross-task leaks.

---

## Test Verification Breakdown

### 1. Unit Tests
- Tested Pydantic validation schemas, missing parameter rejection, wrong argument types, and deterministic tool selection policy across edge cases.

### 2. Mocked Tests
- Tested timeout isolation, server crash simulations, and malformed server response fallback mechanisms.

### 3. Local FastMCP Integration Tests
- Validated genuine FastMCP stdio client/server communication via `stdio_client(StdioServerParameters(command=sys.executable, args=["-m", "testforge.mcp_server", ...]))`.
- Confirmed reading files, retrieving file stats, and listing directories through real stdio transport.

### 4. End-to-End Orchestrator Pipeline Acceptance
- Submitted real tasks (`samples/discount.py`, `samples/banking.py`) through `TestForgeOrchestrator` with active FastMCP clients.
- Verified end-to-end lifecycle progression (`CREATED` -> `INGESTING` -> `PLANNING` -> `GENERATING_TESTS` -> `EVALUATING` -> `COMPLETED`).
- Verified presence of MCP metadata (`source_sha`, `line_count`, `mcp_tool_called`) in Blackboard partitions and trace logs.

---

## Gap Resolution Status
- **GAP-01**: Resolved in Milestone 1.1 (Canonical Task Lifecycle State Machine).
- **GAP-02**: **RESOLVED** in Milestone 1.2 (Real MCP Tool Invocation).
- **GAP-03**: Deferred to Milestone 1.3 (Automatic Checkpoint Resumption) per scope boundary.
